# Copyright 2017 geehalel@gmail.com
#
# This file is part of npindi.
#
#    npindi is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    npindi is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with npindi.  If not, see <http://www.gnu.org/licenses/>.

import base64
import zlib
from collections import OrderedDict

from indi.INDI import INDI, IText, INumber, ISwitch, IBLOB, ILight, IVectorProperty

class BaseDevice:
    _prop_types={
        'TextVector': INDI.INDI_PROPERTY_TYPE.INDI_TEXT,
        'NumberVector': INDI.INDI_PROPERTY_TYPE.INDI_NUMBER,
        'SwitchVector': INDI.INDI_PROPERTY_TYPE.INDI_SWITCH,
        'LightVector': INDI.INDI_PROPERTY_TYPE.INDI_LIGHT,
        'BLOBVector': INDI.INDI_PROPERTY_TYPE.INDI_BLOB
    }
    _elem_def_tags={
        INDI.INDI_PROPERTY_TYPE.INDI_TEXT: 'defText',
        INDI.INDI_PROPERTY_TYPE.INDI_NUMBER: 'defNumber',
        INDI.INDI_PROPERTY_TYPE.INDI_SWITCH: 'defSwitch',
        INDI.INDI_PROPERTY_TYPE.INDI_LIGHT: 'defLight',
        INDI.INDI_PROPERTY_TYPE.INDI_BLOB: 'defBLOB'
    }
    _elem_tags={
        INDI.INDI_PROPERTY_TYPE.INDI_TEXT: 'oneText',
        INDI.INDI_PROPERTY_TYPE.INDI_NUMBER: 'oneNumber',
        INDI.INDI_PROPERTY_TYPE.INDI_SWITCH: 'oneSwitch',
        INDI.INDI_PROPERTY_TYPE.INDI_LIGHT: 'oneLight',
        INDI.INDI_PROPERTY_TYPE.INDI_BLOB: 'oneBLOB'
    }
    def __init__(self):
        self.name=None
        self.mediator=None
        self.logger=None
        self.properties=OrderedDict()
        self.message_log=[]
    def getDeviceName(self):
        return self.name
    def check_message(self, elem):
        message=elem.get('message')
        if not message or message=='':
            return True
        timestamp=elem.get('timestamp')
        if not timestamp or timestamp=='':
            timestamp=time.strftime('%Y-%m-%dT%H:%M:%S')
        self.message_log.append(timestamp+': '+message)
        if self.mediator:
            self.mediator.new_message(self, len(self.message_log) - 1)
        return True
    def message_queue(self, index):
        if abs(index) >= len(self.message_log):
            return ''
        return self.message_log[index]
    def last_message(self):
        return message_log[-1]
    def build_prop(self, elem):
        device_name, prop_name = elem.get('device'), elem.get('name')
        label, group = elem.get('label'), elem.get('group')
        if not self.name or self.name=='':
            self.name=device_name
        if prop_name=='':
            if self.logger: self.logger.error('Empty property name'+elem)
            return INDI.INDI_ERROR_TYPE.INDI_PROPERTY_INVALID
        if prop_name in self.properties:
            if self.logger: self.logger.error('Property duplicated: \''+prop_name+'\' in device '+ device_name)
            return INDI.INDI_ERROR_TYPE.INDI_PROPERTY_DUPLICATED
        prop_type=BaseDevice._prop_types[elem.tag[3:]]
        perm=None
        if prop_type!=INDI.INDI_PROPERTY_TYPE.INDI_LIGHT:
            perm=INDI.crackIndi(elem.get('perm'), INDI.IPerm)
            if not perm:
                if self.logger: self.logger.error('Error extracting '+ prop_name + ' permission: ' + elem.get('perm'))
                return INDI.INDI_ERROR_TYPE.INDI_PROPERTY_INVALID
        rule=None
        if prop_type==INDI.INDI_PROPERTY_TYPE.INDI_SWITCH:
            rule=INDI.crackIndi(elem.get('rule'), INDI.ISRule)
            if not rule:
                rule = INDI.ISRule.ISR_10FMANY
        try:
            timeout=int(elem.get('timeout'))
        except:
            timeout=None
        state=INDI.crackIndi(elem.get('state'), INDI.IPState)
        if not state:
            if self.logger: self.logger.error('Error extracting '+ prop_name + ' state: ' + elem.get('state'))
            return INDI.INDI_ERROR_TYPE.INDI_PROPERTY_INVALID
        timestamp=elem.get('timestamp')
        new_prop=IVectorProperty(self, prop_name, label, group, perm, rule, timeout, state, prop_type, timestamp)
        if perm:
            new_prop.perm=perm
        if rule:
            new_prop.rule=rule
        for pelem in elem.iter(BaseDevice._elem_def_tags[prop_type]):
            pelem_name, pelem_label=pelem.get('name'), pelem.get('label')
            if pelem_name:
                text_value=''.join(pelem.itertext()).strip()
                #print(pelem_name+':'+textvalue)
                if prop_type==INDI.INDI_PROPERTY_TYPE.INDI_SWITCH:
                    switch_state=INDI.crackIndi(text_value, INDI.ISState)
                    new_prop.vp[pelem_name]=ISwitch(pelem_name, pelem_label, switch_state, new_prop)
                elif prop_type==INDI.INDI_PROPERTY_TYPE.INDI_LIGHT:
                    light_state=INDI.crackIndi(text_value, INDI.IPState)
                    new_prop.vp[pelem_name]=ILight(pelem_name, pelem_label, light_state, new_prop)
                elif prop_type==INDI.INDI_PROPERTY_TYPE.INDI_TEXT:
                    new_prop.vp[pelem_name]=IText(pelem_name, pelem_label, text_value, new_prop)
                elif prop_type==INDI.INDI_PROPERTY_TYPE.INDI_NUMBER:
                    numformat=pelem.get('format')
                    minvalue=INDI.f_scan_sexa(pelem.get('min'))
                    maxvalue=INDI.f_scan_sexa(pelem.get('max'))
                    stepvalue=INDI.f_scan_sexa(pelem.get('step'))
                    value=INDI.f_scan_sexa(text_value)
                    new_prop.vp[pelem_name]=INumber(pelem_name, pelem_label, numformat,
                                                    minvalue, maxvalue, stepvalue, value, new_prop)
                elif prop_type==INDI.INDI_PROPERTY_TYPE.INDI_BLOB:
                    blobformat=pelem.get('format')
                    new_prop.vp[pelem_name]=IBLOB(pelem_name, pelem_label, blobformat,
                                                  None, 0, 0, new_prop)
            else:
                if self.logger: self.logger.warn('Property '+ prop_name + ' has element with empty name')
        if len(new_prop.vp) > 0:
            self.properties[prop_name]=new_prop
        else:
            if self.logger: self.logger.warn('new property with no valid members: '+prop_name)
            return INDI.INDI_ERROR_TYPE.INDI_PROPERTY_INVALID
        if self.mediator: self.mediator.new_property(new_prop)
        return True
    def set_value(self, elem):
        device_name, prop_name = elem.get('device'), elem.get('name')
        if prop_name=='':
            if self.logger: self.logger.error('Empty property name'+elem)
            return INDI.INDI_ERROR_TYPE.INDI_PROPERTY_INVALID
        if not prop_name in self.properties:
            if self.logger: self.logger.error('No property \''+prop_name+'\' in device '+ device_name)
            return INDI.INDI_ERROR_TYPE.INDI_PROPERTY_INVALID
        prop=self.properties[prop_name]
        self.check_message(elem)
        state=elem.get('state')
        if state:
            prop.state=INDI.crackIndi(state, INDI.IPState)
        timeout=elem.get('timeout')
        if timeout:
            prop.timeout=timeout
        timestamp=elem.get('timestamp')
        if timestamp:
            prop.timestamp=timestamp
        for pelem in elem.iter(BaseDevice._elem_tags[prop.type]):
            elem_name=pelem.get('name')
            if elem_name:
                if not elem_name in prop.vp:
                    if self.logger: self.logger.warn('Can not set undefined element '+elem_name+' for property '+prop_name)
                    continue
                elem=prop.vp[elem_name]
                text_value=''.join(pelem.itertext()).strip()
                if prop.type==INDI.INDI_PROPERTY_TYPE.INDI_SWITCH:
                    switch_state=INDI.crackIndi(text_value, INDI.ISState)
                    elem.s=switch_state
                elif prop.type==INDI.INDI_PROPERTY_TYPE.INDI_LIGHT:
                    light_state=INDI.crackIndi(text_value, INDI.IPState)
                    elem.s=light_state
                elif prop.type==INDI.INDI_PROPERTY_TYPE.INDI_TEXT:
                    elem.text=text_value
                elif prop.type==INDI.INDI_PROPERTY_TYPE.INDI_NUMBER:
                    minvalue=INDI.f_scan_sexa(pelem.get('min'))
                    maxvalue=INDI.f_scan_sexa(pelem.get('max'))
                    value=INDI.f_scan_sexa(text_value)
                    if minvalue: elem.min=minvalue
                    if maxvalue: elem.max=maxvalue
                    if value: elem.value=value
                elif prop.type==INDI.INDI_PROPERTY_TYPE.INDI_BLOB:
                    blobformat=pelem.get('format')
                    size=pelem.get('size')
                    if blobformat and size:
                        try:
                            blobsize=int(size)
                        except:
                            if self.logger: self.logger.warn('Can not parse blob size for '+elem_name+' in '+prop_name)
                            continue
                        if blobsize==0:
                            if self.mediator: self.mediator.new_BLOB(elem)
                        elem.size=blobsize
                        elem.format=blobformat
                        try:
                            data=base64.b64decode(text_value)
                        except:
                            if self.logger: self.logger.warn('Unable to base64 decode '+elem_name+' in '+prop_name)
                            continue
                        elem.bloblen=len(data)
                        if elem.format[-2:]=='.z':
                            elem.blob=zlib.decompress(data)
                            elem.size=len(elem.blob)
                        else:
                            elem.blob=data
                        if self.mediator: self.mediator.new_blob(elem)
                    else:
                        if self.logger: self.logger.warn('Can not parse blob for '+elem_name+' in '+prop_name)
                        continue
            else:
               if self.logger: self.logger.error('Empty property name'+elem)
               continue
        if self.mediator:
            if prop.type==INDI.INDI_PROPERTY_TYPE.INDI_SWITCH: self.mediator.new_switch(prop)
            if prop.type==INDI.INDI_PROPERTY_TYPE.INDI_LIGHT: self.mediator.new_light(prop)
            if prop.type==INDI.INDI_PROPERTY_TYPE.INDI_TEXT: self.mediator.new_text(prop)
            if prop.type==INDI.INDI_PROPERTY_TYPE.INDI_NUMBER: self.mediator.new_number(prop)
        return True
