import time
from math import ceil
from pathlib import Path

import keyboard
import pyautogui
from loguru import logger

# 0: 不做任何操作，适合单个文件
# 1: 竖屏的pdf，方法先转为横屏，然后全屏，合并成pdf后再转回来
# 2. 横屏ppt
# 3. txt类型的，用作翻页的前置条件+切换上
# 4. 横屏pdf
keyboard.press_and_release('left windows + 2')
logger.info("open success")
time.sleep(5)


def ctrl_tab():
    keyboard.press("ctrl")
    time.sleep(2)
    keyboard.press_and_release("tab")
    time.sleep(2)
    keyboard.release("ctrl")


# _ = [ceil((i / 49)) for i in all_]
# print(_)
file_type = 0
all_ = [1]
for i in range(len(all_)):
    path = Path(f"./temp/{i}")
    path.mkdir(exist_ok=True)
    if file_type == 3:
        # 49 是一个文本编辑器 **全屏** 所展示的行数
        all_ = [ceil((i / 49)) for i in all_]
    for j in range(all_[i]):
        img = pyautogui.screenshot()
        img.save(f'./temp/{i}/{j}.jpg')
        logger.info(f"save {j} success")
        keyboard.press_and_release("pagedown")
        time.sleep(3)
    time.sleep(5)
    # 竖屏的pdf
    if file_type == 1:
        logger.info("竖屏pdf--进入下一个pdf")
        # 退出pdf全屏
        keyboard.press_and_release("esc")
        time.sleep(4)
        # 切换下一个pdf
        ctrl_tab()
        time.sleep(4)
        # 顺时针旋转
        keyboard.press_and_release("ctrl+shift+=")
        time.sleep(4)
        # 进入全屏
        keyboard.press_and_release("ctrl+l")
        time.sleep(6)
    elif file_type == 2:
        logger.info("横屏ppt-进入下一个")
        keyboard.press_and_release("esc")
        time.sleep(4)
        # 切换下一个pdf
        ctrl_tab()
        time.sleep(4)
        keyboard.press_and_release("f5")
        time.sleep(6)
    elif file_type == 3:
        logger.info("文本类型-进入切换")
        time.sleep(3)
        ctrl_tab()
        time.sleep(4)
    elif file_type == 4:
        pass
