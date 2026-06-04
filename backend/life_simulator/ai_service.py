import json
import random
import urllib.request
import urllib.error


OLLAMA_BASE = 'http://localhost:11434'
OLLAMA_MODEL = 'deepseek-r1:1.5b'
MAX_STAGES = 10


def _call_llm(messages):
    url = f"{OLLAMA_BASE}/api/chat"
    payload = json.dumps({
        'model': OLLAMA_MODEL,
        'messages': messages,
        'stream': False,
        'options': {
            'temperature': 0.85,
            'num_predict': 1500,
        }
    }).encode('utf-8')

    req = urllib.request.Request(url, data=payload, headers={
        'Content-Type': 'application/json',
    })

    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            content = data.get('message', {}).get('content', '')
            return _parse_json_response(content)
    except Exception as e:
        print(f"[Ollama Error] {e}")
        return None


def _parse_json_response(content):
    try:
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end > start:
            return json.loads(content[start:end])
    except Exception:
        pass
    return None


def _get_world_prompt(world_type):
    world_desc = {
        'modern': '现代都市',
        'ancient': '古代江湖修仙',
        'future': '未来赛博科幻',
    }
    return world_desc.get(world_type, '现代都市')


def generate_background(world_type):
    llm_result = _call_llm([
        {'role': 'system', 'content': f'''你是一个人生模拟器的角色生成器。世界观是「{_get_world_prompt(world_type)}」。

请为玩家生成一个随机的人生背景，包含：
1. 出身家庭（一句话描述）
2. 天赋（一个独特的优点或特长）
3. 性格（一个形容词）

请严格按JSON格式返回：
{{
  "family": "出身描述（10字以内）",
  "talent": "天赋描述（4字）",
  "personality": "性格描述（4字）"
}}

注意：必须符合「{_get_world_prompt(world_type)}」世界观的背景。'''},
        {'role': 'user', 'content': '请生成一个随机的人生背景。'},
    ])

    if llm_result and 'family' in llm_result and 'talent' in llm_result and 'personality' in llm_result:
        return llm_result

    fallback = {
        'modern': [
            {'family': '普通工薪家庭', 'talent': '学霸体质', 'personality': '沉稳内敛'},
            {'family': '知识分子家庭', 'talent': '艺术天赋', 'personality': '热情开朗'},
            {'family': '商人世家', 'talent': '商业头脑', 'personality': '冷静理性'},
            {'family': '书香门第', 'talent': '超强记忆', 'personality': '浪漫感性'},
            {'family': '富裕家庭', 'talent': '技术天才', 'personality': '坚韧不拔'},
            {'family': '贫困家庭', 'talent': '社交达人', 'personality': '随遇而安'},
        ],
        'ancient': [
            {'family': '武林世家', 'talent': '剑道天赋', 'personality': '侠义心肠'},
            {'family': '皇室旁支', 'talent': '内功奇才', 'personality': '亦正亦邪'},
            {'family': '寒门弟子', 'talent': '炼丹奇才', 'personality': '淡泊名利'},
            {'family': '仙门后裔', 'talent': '轻功卓绝', 'personality': '野心勃勃'},
            {'family': '商贾之子', 'talent': '暗器高手', 'personality': '重情重义'},
            {'family': '孤儿', 'talent': '天生神力', 'personality': '冷面无情'},
        ],
        'future': [
            {'family': '星际贵族', 'talent': '基因强化', 'personality': '探索先锋'},
            {'family': '地球原住民', 'talent': '脑机接口', 'personality': '秩序守卫'},
            {'family': '殖民地开拓者', 'talent': '量子直觉', 'personality': '自由革命者'},
            {'family': 'AI共生家庭', 'talent': '纳米操控', 'personality': '科技信仰者'},
            {'family': '流浪者', 'talent': '时空感知', 'personality': '人性坚守者'},
            {'family': '科研世家', 'talent': 'AI共鸣', 'personality': '进化主义者'},
        ],
    }
    return random.choice(fallback.get(world_type, fallback['modern']))


def generate_initial_story(world_type, attributes, background):
    world_name = _get_world_prompt(world_type)
    llm_result = _call_llm([
        {'role': 'system', 'content': f'''你是一个人生模拟器的剧情引擎。世界观是「{world_name}」。

你的任务是生成游戏开局的第一段剧情。这是一个起点，不需要之前的经历。

请按以下JSON格式返回：
{{
  "stage": "当前人生阶段名称（6字以内）",
  "story": "剧情文本，80-150字，生动有画面感，有伏笔",
  "options": [
    {{"id": 1, "text": "选项描述（10字以内）", "effect": {{"intelligence": 0, "charm": 0, "strength": 0, "luck": 0, "wealth": 0}}}},
    {{"id": 2, "text": "选项描述（10字以内）", "effect": {{"intelligence": 0, "charm": 0, "strength": 0, "luck": 0, "wealth": 0}}}},
    {{"id": 3, "text": "选项描述（10字以内）", "effect": {{"intelligence": 0, "charm": 0, "strength": 0, "luck": 0, "wealth": 0}}}}
  ],
  "event_tag": "本阶段关键词（4字）"
}}

effect数值范围：-3到+3。
选项要体现不同的人生走向。'''},
        {'role': 'user', 'content': f'''玩家背景：
- 出身：{background['family']}
- 天赋：{background['talent']}
- 性格：{background['personality']}

请生成开局剧情。'''},
    ])

    if llm_result:
        return llm_result

    return {
        'stage': '命运起点',
        'story': f'你出生在{background["family"]}。自幼展现出{background["talent"]}的天赋，你的性格{background["personality"]}。命运的齿轮开始转动，你的人生将何去何从？',
        'options': [
            {'id': 1, 'text': '接受命运安排', 'effect': {'intelligence': 1, 'charm': 0, 'strength': 0, 'luck': 1, 'wealth': 0}},
            {'id': 2, 'text': '尝试改变现状', 'effect': {'intelligence': 0, 'charm': 1, 'strength': 1, 'luck': 0, 'wealth': 0}},
            {'id': 3, 'text': '顺其自然发展', 'effect': {'intelligence': 0, 'charm': 0, 'strength': 0, 'luck': 2, 'wealth': 1}},
        ],
        'event_tag': '命运起点',
    }


def generate_next_story(world_type, stage_index, attributes, history, last_choice):
    world_name = _get_world_prompt(world_type)
    history_text = ''
    if history:
        events = [f"第{h['stage_index']+1}阶段：{h.get('event_tag','')}" for h in history]
        history_text = ' → '.join(events[-5:])
        last_event = history[-1]
        last_choice_text = last_event.get('choice_text', '')
        if last_choice_text:
            history_text += f'。你选择了：{last_choice_text}'

    llm_result = _call_llm([
        {'role': 'system', 'content': f'''你是一个人生模拟器的剧情引擎。世界观是「{world_name}」。

这是第{stage_index + 1}阶段（共{MAX_STAGES}阶段）。玩家已经经历了一些人生阶段，你需要根据他/她的选择，生成下一个阶段的剧情。

请按以下JSON格式返回：
{{
  "stage": "当前人生阶段名称（6字以内）",
  "story": "剧情文本，80-150字，生动有画面感，有转折和冲突",
  "options": [
    {{"id": 1, "text": "选项描述（10字以内）", "effect": {{"intelligence": 0, "charm": 0, "strength": 0, "luck": 0, "wealth": 0}}}},
    {{"id": 2, "text": "选项描述（10字以内）", "effect": {{"intelligence": 0, "charm": 0, "strength": 0, "luck": 0, "wealth": 0}}}},
    {{"id": 3, "text": "选项描述（10字以内）", "effect": {{"intelligence": 0, "charm": 0, "strength": 0, "luck": 0, "wealth": 0}}}}
  ],
  "event_tag": "本阶段关键词（4字）"
}}

重要要求：
1. stage必须是全新的、与之前不同的阶段名称，体现人生的起伏变化
2. 可以是：意外转折、重大选择、命运相遇、危机挑战、意外收获等
3. 选项要导致截然不同的人生走向
4. effect数值范围：-3到+3'''},
        {'role': 'user', 'content': f'''玩家当前属性：
- 智力：{attributes['intelligence']}
- 魅力：{attributes['charm']}
- 体质：{attributes['strength']}
- 运气：{attributes['luck']}
- 财富：{attributes['wealth']}

玩家经历：{history_text}

请生成下一阶段剧情。'''},
    ])

    if llm_result:
        return llm_result

    fallback_stages = [
        {'stage': '意外转折', 'event_tag': '命运转折'},
        {'stage': '重大抉择', 'event_tag': '人生路口'},
        {'stage': '命运相遇', 'event_tag': '因果交织'},
        {'stage': '危机挑战', 'event_tag': '生死考验'},
        {'stage': '意外收获', 'event_tag': '福祸相依'},
        {'stage': '巅峰时刻', 'event_tag': '人生巅峰'},
        {'stage': '低谷时期', 'event_tag': '卧薪尝胆'},
        {'stage': '重大决定', 'event_tag': '命运之门'},
    ]
    fs = fallback_stages[stage_index % len(fallback_stages)]

    return {
        'stage': fs['stage'],
        'story': f'人生来到新的十字路口。过去的经历塑造了现在的你，但你面临新的抉择。命运之神正在注视着你接下来的每一步。',
        'options': [
            {'id': 1, 'text': '勇敢前行', 'effect': {'intelligence': 1, 'charm': 0, 'strength': 2, 'luck': 0, 'wealth': 0}},
            {'id': 2, 'text': '谨慎行事', 'effect': {'intelligence': 2, 'charm': 1, 'strength': 0, 'luck': 1, 'wealth': 1}},
            {'id': 3, 'text': '寻求帮助', 'effect': {'intelligence': 0, 'charm': 2, 'strength': 0, 'luck': 2, 'wealth': 0}},
        ],
        'event_tag': fs['event_tag'],
    }


def generate_attributes():
    return {
        'intelligence': random.randint(40, 80),
        'charm': random.randint(40, 80),
        'strength': random.randint(40, 80),
        'luck': random.randint(40, 80),
        'wealth': random.randint(30, 70),
    }


def generate_ending(world_type, attributes, history):
    world_name = _get_world_prompt(world_type)
    history_text = ' → '.join([h.get('event_tag', '') for h in history])
    choices_text = '；'.join([h.get('choice_text', '') for h in history if h.get('choice_text')])

    total = sum(attributes.values())
    level = '传奇' if total > 320 else '精彩' if total > 240 else '平凡' if total > 160 else '坎坷'

    llm_result = _call_llm([
        {'role': 'system', 'content': f'''你是一个人生模拟器的结局生成器。世界观是「{world_name}」。

根据玩家完整的人生经历，生成终局评价。

请按以下JSON格式返回：
{{
  "ending": "终局文本，150-250字，总结玩家一生的故事",
  "score": 0-100的评分整数,
  "title": "命运称号（4字）",
  "tags": ["标签1", "标签2", "标签3"]
}}

要求：
1. ending要情感丰富，有始有终
2. score根据属性总和和人生经历综合评定
3. title要符合「{world_name}」的风格'''},
        {'role': 'user', 'content': f'''玩家最终属性：
- 智力：{attributes['intelligence']}
- 魅力：{attributes['charm']}
- 体质：{attributes['strength']}
- 运气：{attributes['luck']}
- 财富：{attributes['wealth']}

人生轨迹：{history_text}

人生选择：{choices_text}

这是第{len(history)}个阶段。

请生成终局。'''},
    ])

    if llm_result:
        return llm_result

    score = min(99, max(20, total // 4))
    tags = []
    if attributes['intelligence'] > 65: tags.append('智慧超群')
    if attributes['charm'] > 65: tags.append('魅力四射')
    if attributes['strength'] > 65: tags.append('体魄强健')
    if attributes['luck'] > 65: tags.append('天选之人')
    if attributes['wealth'] > 65: tags.append('富甲一方')
    if not tags: tags.append('大器晚成')

    return {
        'ending': f'你的人生走到了终点。回顾这一生，你经历了{len(history)}个阶段，做出了许多选择。属性最终定格在：智{attributes["intelligence"]}、魅{attributes["charm"]}、体{attributes["strength"]}、运{attributes["luck"]}、财{attributes["wealth"]}。{level}人生，这就是你的故事。',
        'score': score,
        'title': f'{level}人生',
        'tags': tags,
    }
