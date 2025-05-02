from src.captcha.image import ImageCaptcha

import random
import time
import os

ROOT = os.path.abspath(os.path.dirname(__file__))
NUMBER = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
ALPHABET_L = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
ALPHABET_U = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
ALL_CHAR_SET = NUMBER + ALPHABET_L + ALPHABET_U
PIC_AMOUNT = 10
CHAR_AMOUNT = 4  # 每个验证码4字符


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
    path = os.path.join(ROOT, "demo", "run{start_time}".format(start_time=start_time))
    if not os.path.exists(path):
        os.makedirs(path)
    print("Pics and class.txt will be save to {0}".format(path))

    captcha = ImageCaptcha(width=200, height=100, class_type=ALL_CHAR_SET)
    text_list = random_text(ALL_CHAR_SET)
    for text in text_list:
        filepath = os.path.join(path, '{char}_{now_time}.png'.format(now_time=str(int(time.time())), char=text))
        captcha.write(text, filepath)
        assert os.path.isfile(filepath)

    captcha.write_class(os.path.join(path, "classes.txt"))


create_database()
