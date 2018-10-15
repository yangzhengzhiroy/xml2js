#!/usr/bin/env python
import re
from lxml import etree
from lxml.etree import tostring
from lxml.etree import XMLParser
from collections import OrderedDict


class LevelError(Exception):
    pass


def xml_text(element, strip_cdata=False, compact=False, remove_blank_text=True):
    """
    This function extracts all root texts in the element (no children's text).
    :param element: etree._Element object,
    :param strip_cdata: bool, whether to parse CDATA as pure text or CDATA text,
    :param compact: bool, whether output JSON in compact format,
    :param remove_blank_text: bool, whether to remove empty text from all text fields,
    :return: OrderedDict().
    """
    try:
        output = OrderedDict(_cdata=[], _text=[]) if compact else []
        element_str = tostring(element).decode()
        text_iter = (text.strip() for text in element.xpath('text()'))
        if remove_blank_text:
            text_iter = (text for text in text_iter if text)
        iter_count = 0
        for text in text_iter:
            cdata = f'![CDATA[{text}]]' in element_str if not strip_cdata else False
            if compact:
                if cdata:
                    output['_cdata'].append(text)
                else:
                    output['_text'].append(text)
            else:
                if cdata:
                    output.append(OrderedDict(type='cdata', cdata=text))
                else:
                    output.append(OrderedDict(type='text', text=text))
            iter_count += 1
        if compact:
            if not output['_cdata']:
                output.pop('_cdata')
            elif len(output['_cdata']) == 1:
                output.update(_cdata=output['_cdata'][0])
            if not output['_text']:
                output.pop('_text')
            elif len(output['_text']) == 1:
                output.update(_text=output['_text'][0])
        output = output if iter_count else None
        return output
    except Exception as e:
        return Exception(e)


def leafelement(element, strip_cdata=False, compact=False, remove_blank_text=True):
    """
    This function converts lowest level tree/etree element to dict structure.
    :param element: etree leaf-level object,
    :param strip_data: bool, whether to parse CDATA as pure text or CDATA text,
    :param compact: bool, whether output JSON in compact format,
    :return: OrderedDict().
    """
    try:
        output = OrderedDict()
        if element.getchildren():
            raise LevelError('The element is not at the lowest level.')
        if isinstance(element, etree._ProcessingInstruction):
            proc_inst = tostring(element).decode()
            name = re.search('<\?[^\s]+', proc_inst)
            name = re.sub('<\?', '', name.group()) if name else ""
            instruction = re.search(' [^=\s]+\?>$', proc_inst)
            instruction = instruction.group()[:-2].strip() if instruction else ""
            if compact:
                output.update(_instruction=OrderedDict(name=instruction))
            else:
                output.update(type='instruction', name=name, instruction=instruction)
            attributes = OrderedDict(element.attrib)
            if attributes:
                output.update(attributes=attributes)
        elif isinstance(element, etree._Comment):
            comment = element.text
            if compact:
                output.update(_comment=comment)
            else:
                output.update(type='comment', comment=comment)
        elif isinstance(element, etree._Element):
            tag = element.tag
            attributes = element.attrib
            text_output = xml_text(element, strip_cdata, compact, remove_blank_text)
            if compact:
                output[tag] = OrderedDict()
                if attributes:
                    output[tag].update(_attributes=OrderedDict(attributes))
                if text_output:
                    output[tag].update(text_output)
            else:
                output.update(type='element', name=tag)
                if attributes:
                    output.update(attributes=OrderedDict(attributes))
                if text_output:
                    output.update(elements=text_output)
        else:
            raise TypeError('The input element has invalid type.')
        return output
    except Exception as e:
        return Exception(e)


def parseelement(element, strip_cdata=False, header=True, compact=False, remove_blank_text=True):
    """
    This function wraps the leaf parsing and recursively parses the whole xml.
    :param element: etree.ElementTree object,
    :param strip_cdata: bool, whether to parse CDATA as pure text or CDATA text,
    :param header: bool, whether to include header info in the JSON,
    :param compact: bool, whether output JSON in compact format,
    :param remove_blank_text: bool, whether to remove empty text from all text fields,
    :return: OrderedDict().
    """
    try:
        output = OrderedDict()
        tag = element.tag
        attributes = element.attrib
        text_output = xml_text(element, strip_cdata, compact, remove_blank_text)
        if compact:
            if header:
                output.update(_declaration=OrderedDict(_attributes=OrderedDict(version='1.0', encoding='ISO-8859-1')))
            if not element.getchildren():
                output.update(leafelement(element, strip_cdata, compact))
                return output
            output.update({tag: OrderedDict()})
            if attributes:
                output[tag].update(_attributes=OrderedDict(attributes))
            if text_output:
                output[tag].update(text_output)
            for child in element.iterchildren():
                update_info = parseelement(child, strip_cdata, False, compact)
                key = list(update_info.keys())[0]
                if key in output[tag]:
                    if not isinstance(output[tag][key], list):
                        output[tag][key] = [output[tag][key]]
                    output[tag][key].append(update_info[key])
                else:
                    output[tag].update(update_info)
        else:
            if header:
                output.update(declaration=OrderedDict(attributes=OrderedDict(version='1.0', encoding='ISO-8859-1')))
            output.update(elements=[])
            if not element.getchildren():
                output['elements'].append(leafelement(element, strip_cdata, compact))
                return output
            output['elements'].append(OrderedDict(type='element', name=tag))
            if attributes:
                output['elements'][0].update(attributes=OrderedDict(attributes))
            output['elements'][0].update(elements=[])
            if text_output:
                output['elements'][0]['elements'].extend(xml_text(element, strip_cdata, compact, remove_blank_text))
            for child in element.iterchildren():
                output['elements'][0]['elements'].extend(parseelement(child, strip_cdata, False, compact)['elements'])
        return output
    except Exception as e:
        return Exception(e)


def xml2json(xml, parser=None, strip_cdata=False, remove_comments=False, remove_pis=False, header=True,
             compact=False, remove_blank_text=True):
    if not isinstance(xml, str) and not isinstance(xml, bytes):
        raise TypeError('The input xml not string or byte format.')
    if not parser:
        parser = XMLParser(remove_comments=remove_comments, remove_pis=remove_pis, strip_cdata=strip_cdata)
    return parseelement(etree.fromstring(xml, parser=parser), strip_cdata=strip_cdata, header=header, compact=compact,
                        remove_blank_text=remove_blank_text)
