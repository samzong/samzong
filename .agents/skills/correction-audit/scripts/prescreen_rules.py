import re

KEYWORDS = r'不对|错了|错误|不是|不需要|不要|不应该|没必要|不接受|不满意|不好|不行|糟糕|太复杂|废话|冗余|\bADHD\b|我的意思|我的本意|我只是|只需要|只关注|只.*(?:即可|就好)|不符合|违[反背]|改坏|缺少|漏了|没了|没做到|没有.*(?:完成|成功|看到)|还是.*(?:问题|不|失败)|还有.*问题|未.*同意|未经|你.*(?:理解|判断|结论|方案|写|改)|\b(?:wrong|incorrect|instead|not what|too complex|too much|unnecessary)\b|去掉|删掉|有问题|卡着|不能|只是.*(?:例子|举例|随口)|说中文|改动.*(?:大|多)|不可接受|没太懂|太限制|其实|实质|理解.*需求|一句话|直白|不合理|太.*(?:快|慢|难看)|没有.*(?:观点|完整版|意义)|不该|不用|workaround|应该只|看不到|没处理|没意义|不合适|不见|不喜欢|不够|等等|当前.*(?:应该|问题)'
INJECTION = r'(?i)(operationId|角色通用约束|<environment_context>|# AGENTS.md instructions|<task-notification>|Lody Operation .* finished|Message Type:|\[confer\]|You are .*agent|你是.*(?:Research|Build|Review) (?:Deep|Fast|Standard))'
ACK = r'(?i)^(?:好[的吧]?|可以|继续|是[的]?|同意|确定|确认|开干|开始|ok(?:ay)?|yes|go|done|谢谢|收到|继续推进|\$\w+|/\w+)[！!。，,.\s]*$'


def reason(user):
    text = user['text']
    if user['nth_user'] == 1:
        return 'first_user'
    if re.search(INJECTION, text):
        return 'injection_marker'
    if re.fullmatch(ACK, text.strip()):
        return 'ack'
    if re.search(KEYWORDS, text, re.I):
        return 'candidate'
    return 'no_signal'
