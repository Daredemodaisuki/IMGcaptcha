# coding: utf-8

import os
from src.captcha.image import ImageCaptcha

ROOT = os.path.abspath(os.path.dirname(__file__))


def test_image_generate():
    captcha = ImageCaptcha()
    data = captcha.generate('1234')
    assert hasattr(data, 'read')


def test_save_image():
    captcha = ImageCaptcha()
    filepath = os.path.join(ROOT, 'demo/demo.png')
    captcha.write('1145141919810', filepath)
    assert os.path.isfile(filepath)

    captcha.write_class(os.path.join(ROOT, "demo/demo_class.txt"))

test_save_image()