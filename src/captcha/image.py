# coding: utf-8
"""
    captcha.image
    ~~~~~~~~~~~~~

    Generate Image CAPTCHAs, just the normal image CAPTCHAs you are using.
"""

from __future__ import annotations
import os
import secrets
import typing as t
from PIL.Image import new as createImage, Image, Transform, Resampling
from PIL.ImageDraw import Draw, ImageDraw
from PIL.ImageFilter import SMOOTH
from PIL.ImageFont import FreeTypeFont, truetype
from io import BytesIO

__all__ = ['ImageCaptcha']

ColorTuple = t.Union[t.Tuple[int, int, int], t.Tuple[int, int, int, int]]

DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')
DEFAULT_FONTS = [os.path.join(DATA_DIR, 'DroidSansMono.ttf')]


class ImageCaptcha:
    """Create an image CAPTCHA.

    Many of the codes are borrowed from wheezy.captcha, with a modification
    for memory and developer friendly.

    ImageCaptcha has one built-in font, DroidSansMono, which is licensed under
    Apache License 2. You should always use your own fonts::

        captcha = ImageCaptcha(fonts=['/path/to/A.ttf', '/path/to/B.ttf'])

    You can put as many fonts as you like. But be aware of your memory, all of
    the fonts are loaded into your memory, so keep them a lot, but not too
    many.

    :param width: The width of the CAPTCHA image.
    :param height: The height of the CAPTCHA image.
    :param fonts: Fonts to be used to generate CAPTCHA images.
    :param font_sizes: Random choose a font size from this parameters.
    """
    lookup_table: list[int] = [int(i * 1.97) for i in range(256)]
    character_offset_dx: tuple[int, int] = (0, 4)
    character_offset_dy: tuple[int, int] = (0, 6)
    character_rotate: tuple[int, int] = (-30, 30)
    character_warp_dx: tuple[float, float] = (0.1, 0.3)
    character_warp_dy: tuple[float, float] = (0.2, 0.3)
    word_space_probability: float = 0.5
    word_offset_dx: float = 0.25

    def __init__(
            self,
            width: int = 160,
            height: int = 60,
            fonts: list[str] | None = None,
            font_sizes: tuple[int, ...] | None = None,
            class_type: list[str] | None = None,
            auto_add_class: bool = True):
        self._width = width
        self._height = height
        self._fonts = fonts or DEFAULT_FONTS
        self._font_sizes = font_sizes or (42, 50, 56)
        self._truefonts: list[FreeTypeFont] = []
        # 改动说明：添加类别表
        self._class_type = [] if class_type is None else class_type
        self._auto_add_class = auto_add_class

    @property
    def truefonts(self) -> list[FreeTypeFont]:
        if self._truefonts:
            return self._truefonts
        self._truefonts = [
            truetype(n, s)
            for n in self._fonts
            for s in self._font_sizes
        ]
        return self._truefonts

    @staticmethod
    def create_noise_curve(image: Image, color: ColorTuple) -> Image:
        w, h = image.size
        x1 = secrets.randbelow(int(w / 5) + 1)
        x2 = secrets.randbelow(w - int(w / 5) + 1) + int(w / 5)
        y1 = secrets.randbelow(h - 2 * int(h / 5) + 1) + int(h / 5)
        y2 = secrets.randbelow(h - y1 - int(h / 5) + 1) + y1
        points = [x1, y1, x2, y2]
        end = secrets.randbelow(41) + 160
        start = secrets.randbelow(21)
        Draw(image).arc(points, start, end, fill=color)
        return image

    @staticmethod
    def create_noise_dots(
            image: Image,
            color: ColorTuple,
            width: int = 3,
            number: int = 30) -> Image:
        draw = Draw(image)
        w, h = image.size
        while number:
            x1 = secrets.randbelow(w + 1)
            y1 = secrets.randbelow(h + 1)
            draw.line(((x1, y1), (x1 - 1, y1 - 1)), fill=color, width=width)
            number -= 1
        return image

    def _draw_character(
            self,
            c: str,
            draw: ImageDraw,
            color: ColorTuple) -> tuple[Image, dict[str, int]]:
        font = secrets.choice(self.truefonts)
        _, _, w, h = draw.multiline_textbbox((1, 1), c, font=font)

        dx1 = secrets.randbelow(self.character_offset_dx[1] - self.character_offset_dx[0] + 1) + \
              self.character_offset_dx[0]
        dy1 = secrets.randbelow(self.character_offset_dy[1] - self.character_offset_dy[0] + 1) + \
              self.character_offset_dy[0]
        im = createImage('RGBA', (int(w) + dx1, int(h) + dy1))
        Draw(im).text((dx1, dy1), c, font=font, fill=color)

        # rotate
        im = im.crop(im.getbbox())
        im = im.rotate(
            self.character_rotate[0] + (secrets.randbits(32) / (2 ** 32)) * (
                        self.character_rotate[1] - self.character_rotate[0]),
            Resampling.BILINEAR,
            expand=True,
        )

        # warp
        dx2 = w * (secrets.randbits(32) / (2 ** 32)) * (self.character_warp_dx[1] - self.character_warp_dx[0]) + \
              self.character_warp_dx[0]
        dy2 = h * (secrets.randbits(32) / (2 ** 32)) * (self.character_warp_dy[1] - self.character_warp_dy[0]) + \
              self.character_warp_dy[0]
        x1 = int(secrets.randbits(32) / (2 ** 32) * (dx2 - (-dx2)) + (-dx2))
        y1 = int(secrets.randbits(32) / (2 ** 32) * (dy2 - (-dy2)) + (-dy2))
        x2 = int(secrets.randbits(32) / (2 ** 32) * (dx2 - (-dx2)) + (-dx2))
        y2 = int(secrets.randbits(32) / (2 ** 32) * (dy2 - (-dy2)) + (-dy2))
        w2 = w + abs(x1) + abs(x2)
        h2 = h + abs(y1) + abs(y2)
        data = (
            x1, y1,
            -x1, h2 - y2,
            w2 + x2, h2 + y2,
            w2 - x2, -y1,
        )
        im = im.resize((int(w2), int(h2)))
        # 改动说明：transform(_, Transform.QUAD, data)方法对图像进行四边形变换，将图像的四边形区域映射到另一个四边形区域
        # 所以可以通过data的四至给出最终单个字符在img的bbox
        im = im.transform((int(w), int(h)), Transform.QUAD, data)
        bbox = {"x_min": min(x1, -x1, int(w2) + x2, int(w2) - x2),
                "x_max": max(x1, -x1, int(w2) + x2, int(w2) - x2),
                "y_min": min(y1, int(h2) - y2, int(h2) + y2, -y1),  # 下界？
                "y_max": max(y1, int(h2) - y2, int(h2) + y2, -y1)}
        return im, bbox

    def create_captcha_image(
            self,
            chars: str,
            color: ColorTuple,
            background: ColorTuple) -> tuple[Image, list[dict[str, int | str | dict[str | int]]]]:
        """Create the CAPTCHA image itself.

        :param chars: text to be generated.
        :param color: color of the text.
        :param background: color of the background.

        The color should be a tuple of 3 numbers, such as (0, 255, 255).
        """
        image = createImage('RGB', (self._width, self._height), background)
        draw = Draw(image)

        # 改动说明：因为前面加了bbox，这里对应修改，记录每个字符切片里面字符在切片的bbox
        # bbox_info是list，每项是一个dict，dict包括：
        #   char：因为后面要生成随机空格，所以需要记录最终字符
        #   char_bbox_in_image：字符在字符切片bbox
        #   image_bbox：字符切片在验证码图像中的bbox
        bbox_info: list[dict[str, int | str | dict[str | int]]] = []

        images: list[Image] = []  # 字符切片图像
        for c in chars:
            if secrets.randbits(32) / (2 ** 32) > self.word_space_probability:
                blank, blank_bbox = self._draw_character(" ", draw, color)
                images.append(blank)
                bbox_info.append({
                    "char": " ",
                    "char_bbox_in_image": blank_bbox
                })
            character, character_bbox = self._draw_character(c, draw, color)
            images.append(character)
            bbox_info.append({
                "char": c,
                "char_bbox_in_image": character_bbox
            })

        text_width = sum([im.size[0] for im in images])

        # 如果字符切片的总宽超出设定验证码图像宽度，先用着总宽，最后再resize回设定宽度
        width = max(text_width, self._width)
        image = image.resize((width, self._height))

        # 通过offset确定每个字符切片在验证码图像中的位置
        average = int(text_width / len(chars))  # 每个字符所需平均宽度（字符数不含在随机加的空格）
        rand = int(self.word_offset_dx * average)  # 最大偏移量：self.word_offset_dx是一个比例系数
        offset = int(average * 0.1)  # 第0个字符切片偏移量（避免字符太靠近边缘）

        for i in range(len(images)):
            w, h = images[i].size
            mask = images[i].convert('L').point(self.lookup_table)
            image.paste(images[i], (offset, int((self._height - h) / 2)), mask)
            # 记录每个字符切片在验证码图像中的位置
            bbox_info[i].update({"image_bbox": {
                    "x_min": offset,
                    "x_max": offset + w,
                    "y_min": int((self._height - h) / 2),
                    "y_max": int((self._height - h) / 2) + h
                },
                "char_bbox_in_pic": {
                    "x_min": offset + bbox_info[i]["char_bbox_in_image"]["x_min"],
                    "x_max": offset + bbox_info[i]["char_bbox_in_image"]["x_max"],
                    "y_min": int((self._height - h) / 2) + bbox_info[i]["char_bbox_in_image"]["y_min"],
                    "y_max": int((self._height - h) / 2) + bbox_info[i]["char_bbox_in_image"]["y_max"]
                }
            })
            # 下一个字符切片offset
            offset = offset + w + (-secrets.randbelow(rand + 1))

        if width > self._width:
            image = image.resize((self._width, self._height))
            for i in range(len(images)):
                bbox_info[i]["char_bbox_in_pic"]["x_min"] = int(
                    bbox_info[i]["char_bbox_in_pic"]["x_min"] * self._width / width)
                bbox_info[i]["char_bbox_in_pic"]["x_max"] = int(
                    bbox_info[i]["char_bbox_in_pic"]["x_max"] * self._width / width)
                # 高没有变化

        return image, bbox_info

    def generate_image(self, chars: str,
                       bg_color: ColorTuple | None = None,
                       fg_color: ColorTuple | None = None) -> tuple[Image, list[dict[str, int | str | dict[str | int]]]]:
        """Generate the image of the given characters.

        :param chars: text to be generated.
        :param bg_color: background color of the image in rgb format (r, g, b).
        :param fg_color: foreground color of the text in rgba format (r,g,b,a).
        """
        # 改动说明：判断字符是否在类别表内，不在则添加
        if self._auto_add_class:
            for char in chars:
                if char not in self._class_type:
                    self._class_type.append(char)

        background = bg_color if bg_color else random_color(238, 255)
        random_fg_color = random_color(10, 200, secrets.randbelow(36) + 220)
        color: ColorTuple = fg_color if fg_color else random_fg_color

        im, bbox_info = self.create_captcha_image(chars, color, background)
        self.create_noise_dots(im, color)
        self.create_noise_curve(im, color)
        im = im.filter(SMOOTH)
        return im, bbox_info

    def label_bbox(self, class_list: list[str],
                   bbox_info: list[dict[str, int | str | dict[str | int]]]
                   ) -> list[list[int | list[float, float]]]:
        # Yolo标注格式：
        #   每个目标对象的类别编号
        #   目标对象在图像中的中心位置(x, y)
        #   目标对象的宽度和高度(w, h)
        label: list[list[int, list[float, float], list[float, float]]] = []
        for bbox in bbox_info:
            char = bbox["char"]
            if char != " " and char in class_list:
                class_type = class_list.index(char)
                center = [(bbox["char_bbox_in_pic"]["x_min"] + bbox["char_bbox_in_pic"]["x_max"]) / 2 / self._width,
                          (bbox["char_bbox_in_pic"]["y_min"] + bbox["char_bbox_in_pic"]["y_max"]) / 2 / self._height]
                size = [(bbox["char_bbox_in_pic"]["x_max"] - bbox["char_bbox_in_pic"]["x_min"]) / self._width,
                        (bbox["char_bbox_in_pic"]["y_max"] - bbox["char_bbox_in_pic"]["y_min"]) / self._height]
                label.append([class_type, center, size])
        return label

    # 这个函数不保存文件，暂时不改bbox相关
    def generate(self, chars: str, format: str = 'png',
                 bg_color: ColorTuple | None = None,
                 fg_color: ColorTuple | None = None) -> BytesIO:
        """Generate an Image Captcha of the given characters.

        :param chars: text to be generated.
        :param format: image file format
        :param bg_color: background color of the image in rgb format (r, g, b).
        :param fg_color: foreground color of the text in rgba format (r,g,b,a).
        """
        im, _ = self.generate_image(chars, bg_color=bg_color, fg_color=fg_color)
        out = BytesIO()
        im.save(out, format=format)
        out.seek(0)
        return out

    def write(self, chars: str, output: str, format: str = 'png',
              bg_color: ColorTuple | None = None,
              fg_color: ColorTuple | None = None) -> None:
        """Generate and write an image CAPTCHA data to the output.

        :param chars: text to be generated.
        :param output: output destination.
        :param format: image file format
        :param bg_color: background color of the image in rgb format (r, g, b).
        :param fg_color: foreground color of the text in rgba format (r,g,b,a).
        """
        im, bbox_info = self.generate_image(chars, bg_color=bg_color, fg_color=fg_color)
        im.save(output, format=format)
        print("Captcha pic is saved to:{0}".format(output))

        # 改动说明：path部分
        pic_path_name, _ = os.path.splitext(output)
        label = ""
        label_info = self.label_bbox(self._class_type, bbox_info)
        for char in label_info:
            label = label + str(char[0])\
                    + " " + str(char[1][0]) + " " + str(char[1][1])\
                    + " " + str(char[2][0]) + " " + str(char[2][1])\
                    + "\n"
        with open(pic_path_name + ".txt", "w") as txt:
            txt.write(label)

    def write_class(self, output: str) -> None:
        class_info = "\n".join(self._class_type)
        with open(output, "w") as txt:
            txt.write(class_info)
            print("Class info is saved to:{0}".format(output))


def random_color(
        start: int,
        end: int,
        opacity: int | None = None) -> ColorTuple:
    red = secrets.randbelow(end - start + 1) + start
    green = secrets.randbelow(end - start + 1) + start
    blue = secrets.randbelow(end - start + 1) + start
    if opacity is None:
        return red, green, blue
    return red, green, blue, opacity
