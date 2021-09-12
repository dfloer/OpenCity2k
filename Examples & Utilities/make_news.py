import argparse
import json
from random import randint
import re
from pprint import pprint
from functools import reduce

def parse_command_line():
    """
    Set up command line arguments.
    Args:
        None.
    Returns:
        Argparse object for setting up command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest="input_file", help="path to json output of data_usa_parse.py", metavar="PATH", required=True)
    parser.add_argument('-o', '--output', dest="output_file", help="output file, or stdout if omitted", metavar="FILE", required=False)
    parser.add_argument('-s', '--story-type', dest="story_type", help="story type to create, 0-66 inclusive", metavar="STORY", required=False)
    parser.add_argument('-m', '--mayor', dest="mayor", help="Mayor's name.", metavar="NAME", required=False)
    parser.add_argument('-c', '--city', dest="city", help="city's name", metavar="CITY", required=False)
    parser.add_argument('-t', '--team', dest="team", help="name of a sports team", metavar="TEAM", required=False)
    args = parser.parse_args()
    return args



def generate_story(raw_tokens, story_type, mayor, city, team, fed_rate):
    if 0 > story_type > 66:
        raise AssertionError("Story type must be between 0 and 82 inclusive.")
    idx = list(raw_tokens.keys())[story_type]
    story_group = raw_tokens[idx]
    base_story = story_group[randint(0, len(story_group) - 1)]
    raw_tokens["mayorname"] = mayor
    raw_tokens["cityname"] = city
    raw_tokens["teamname"] = team

    try:
        headline_text, body = base_story.split('+', 1)
    except ValueError as e:
        print("+?", "+" in base_story, "len", len(base_story.split('+')), "cnt", base_story.count('+'))
        print(base_story)
        raise ValueError(e)
        # if "dateline" in base_story:


    filled_headline = tokens_fill(headline_text, raw_tokens, headline=True)
    filled_story = tokens_fill(body, raw_tokens, {}, headline=False)
    # print("filled:", [filled_story])

    final_body = format_story(filled_story, fed_rate)
    final_headline = format_headline(filled_headline, fed_rate)

    final_story = final_headline + final_body
    return final_story

def format_headline(headline, fed_rate):
    headline = headline.title() + ' -'
    headline = number_replace(headline, fed_rate)
    return headline

def format_story(story, fed_rate):
    # Because re.sub() escapes the single quotes.
    no_escape = story.replace("\\'", "'")

    # find dashes that are between two words. We don't want to change those to paragraph breaks.
    if "MisSim" not in story:
        no_escape = no_escape.replace("--", "zqzdbldashzqz")
    else:
        no_escape = no_escape.replace("--", "\n\t\n\t")
    inline_dashes = [x.start() + 1 for x in re.finditer(r"\w(?<!-)-(?!-)\w", no_escape)]
    no_escape = list(no_escape)
    for x in inline_dashes:
        no_escape[x] = "|"
    safe_dashes_replaced = ''.join(no_escape)
    dashes_or_para = safe_dashes_replaced.replace("-", "\n\t").replace("|", "-")
    dashes_or_para = dashes_or_para.replace("zqzdbldashzqz", "--")

    # This is needed or else the double quote ended up in the wrong spot.
    body = dashes_or_para.replace('."', "zqzdblq.")
    # Ellipsis should be retained.
    body_periods = [x for x in body.replace("...", "zqzellipsiszqz").split('.')]
    body_caps = []
    for idx in range(len(body_periods)):
        y = [x for x in body_periods[idx].split(' ') if x not in ('', ' ')]
        if not y:
            continue
        # This workaround is because title() treats any non alphanumeric character as a word break.
        # "we've" should be "We've" not "We'Ve".
        y[0] = y[0].replace("'", 'zzqzz').title().replace("zzqzz", "'").replace("Zzqzz", "'")
        body_caps += [' '.join(y)]
    # Add the periods and spaces back, and add back the removed trailing space.
    body_caps = '. '.join(body_caps).replace("zqzellipsiszqz", "...") + '.'
    # put the double quote back.
    body_dashes_quotes = body_caps.replace("|", "-").replace("zqzdblq", '"').replace("Zqzdblq", '"')
    # Replace any numbers.
    result = number_replace(body_dashes_quotes, fed_rate)
    if "zqz" in result.lower():
        print("result")
        print(result)
        assert "zqz" not in result
        assert "Zqz" not in result
    return result



def tokens_fill(base_story, raw_tokens, story_tokens={}, headline=False):
    if '{' not in base_story:
        return base_story
        # TODO: handle headline special case for {*x} replacements.
        # These should propogate into the story.
    s = re.compile(r"{(.*?)}")
    r = list(re.finditer(s, base_story))
    token_idxs = [x.span() for x in r]
    tokens = [x[1] for x in r]

    replaced_tokens, story_tokens = token_lookup(tokens, raw_tokens, story_tokens)

    replaced_string = token_replace(base_story, replaced_tokens, token_idxs)

    return tokens_fill(replaced_string, raw_tokens, story_tokens, headline)

def token_replace(replace_in, replacements, token_idxs):
    out = []
    offset = 0
    for idx, (a, b) in enumerate(token_idxs):
        x = replace_in[offset : a]
        y = replacements[idx]
        offset = b
        out += [x]
        out += [y]
    out += replace_in[offset : ]
    return ''.join(out)

def token_lookup(tokens, raw_tokens, previous={}, headline=False):
    output = []
    for t in tokens:
        t = t.replace('{', '').replace('}', '')
        repeat = True

        if not t[0].isalpha():
            v = t[0]
            if v in '*' and not headline:
                ("rep", repeat, headline)
                repeat = False
            # {^replacement} is a different value than {replacement}
            group =  raw_tokens[t[1 : ].lower()]
        else:
            group = raw_tokens[t.lower()]
        if not repeat:
            new_token = group[randint(0, len(group) - 1)]
        else:
            new_token = previous.get(t, None)
            if not new_token:
                new_token = group[randint(0, len(group) - 1)]
                previous[t] = new_token
        output += [new_token]
    return output, previous

def number_replace(token, fed_rate):
    if token.startswith('<'):
        tmp = token.split(' ')
        limit = int(tmp[0][1 : ].replace(',', ''))
        val = [str(randint(1, limit))] + tmp[1 : ]
        return ' '.join(val)
    elif '%' in token:
        n = re.compile(r"%{1}?[0-9]+")
        r = list(re.finditer(n, token))
        vals = [int(x[0].replace("%", '')) for x in r]
        rvals = [str(randint(1, x)) for x in vals]
        for q in rvals:
            token = re.sub(n, q, token, count=1)
    # Special case for the fed rate in body.
    frc = re.compile(r"[$][%](?!\d)")
    fr = list(re.findall(frc, token))
    assert len(fr) <= 1
    token = re.sub(frc, fed_rate + '%', token, count=1)
    return token



def main():
    options = parse_command_line()

    input_path = options.input_file
    output_path = options.output_file
    story_type = options.story_type
    mayor = options.mayor
    city = options.city
    team = options.team

    if not team:
        team = ["Llamas", "Alpacas", "Camels", "Army Ants"][randint(0, 3)]
    if not mayor:
        mayor = "De Facto"
    if not city:
        city = ["Maxisland", "Lakeland", "Happyland", "Volcano"][randint(0, 3)]
    if not story_type:
        story_type = randint(0, 66)
    story_type = int(story_type)
    with open(input_path, 'r') as f:
        text = json.load(f)

    fed_rate = str(randint(1, 10))
    story_text = generate_story(text, story_type, [mayor], [city], [team], fed_rate)

    if output_path:
        with open(output_path, 'w') as f:
            f.write(story_text)
    print(story_text)

if __name__ == "__main__":
    main()
