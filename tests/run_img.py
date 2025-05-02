from src.captcha.image import ImageCaptcha

import random
import time
import os
from tqdm import tqdm

ROOT = os.path.abspath(os.path.dirname(__file__))
NUMBER = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
ALPHABET_L = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
ALPHABET_U = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
ALL_CHAR_SET = NUMBER + ALPHABET_L + ALPHABET_U
PIC_AMOUNT = 20000
CHAR_AMOUNT = 4  # 每个验证码4字符
WIDTH = 200
HEIGHT = 100


def random_text(char_set: list[str], pic_amount: int = 10, char_amount: int = 4) -> list[str]:
    text_list = []
    for i in range(pic_amount):
        captcha_text = []
        for j in range(char_amount):
            c = random.choice(char_set)
            captcha_text.append(c)
        text_list.append(''.join(captcha_text))
    return text_list


def create_database():
    start_time = str(int(time.time()))
    path = os.path.join(ROOT, "demo", "{amount}pic_{w}x{h}_{char_amount}char_at{start_time}".format(
        amount=PIC_AMOUNT,
        w=WIDTH,
        h=HEIGHT,
        char_amount=CHAR_AMOUNT,
        start_time=start_time,
    ))
    if not os.path.exists(path):
        os.makedirs(path)
    print("Pics and class.txt will be save to {0}".format(path))

    captcha = ImageCaptcha(width=WIDTH, height=HEIGHT, class_type=ALL_CHAR_SET)
    text_list = random_text(ALL_CHAR_SET, pic_amount=PIC_AMOUNT, char_amount=CHAR_AMOUNT)

    with tqdm(total=len(text_list), ncols=150) as _tqdm:
        for text in text_list:
            file_name = '{char}_{now_time}.png'.format(now_time=str(int(time.time())), char=text)
            filepath = os.path.join(path, file_name)
            captcha.write(text, filepath)
            assert os.path.isfile(filepath)

            _tqdm.set_postfix({"now": file_name})
            _tqdm.update(1)

    captcha.write_class(os.path.join(path, "classes.txt"))


create_database()
