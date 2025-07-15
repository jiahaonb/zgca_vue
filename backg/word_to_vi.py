from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath
import requests
from dashscope import ImageSynthesis
import os

def text_to_image(prompt, save_dir='./output'):
    print('----sync call, please wait a moment----')
    rsp = ImageSynthesis.call(
        api_key="sk-bba8d81c77b14d59b41e585570d86e7c",
        model="wanx2.0-t2i-turbo",
        prompt=prompt,
        n=1,
        size='1024*1024'
    )
    print('response: %s' % rsp)
    if rsp.status_code == HTTPStatus.OK:
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        for result in rsp.output.results:
            file_name = PurePosixPath(unquote(urlparse(result.url).path)).parts[-1]
            save_path = os.path.join(save_dir, file_name)
            with open(save_path, 'wb+') as f:
                f.write(requests.get(result.url).content)
            print(f"图片已保存到: {save_path}")
        return save_path
    else:
        print('sync_call Failed, status_code: %s, code: %s, message: %s' % 
              (rsp.status_code, rsp.code, rsp.message))
        return None

if __name__ == '__main__':
    # 读入一段内容作为prompt
    prompt = input("请输入用于生成图片的描述内容：")
    save_dir = input("请输入图片保存的文件夹路径（默认output）：").strip() or './output'
    text_to_image(prompt, save_dir)