import asyncio
import datetime
from typing import Tuple, List

import aiohttp
import numpy as np
import pandas as pd
from loguru import logger


# logger.add("./a.log")

def run_time_wraps(func):
    def wrapper(*args, **kwargs):
        start_time = datetime.datetime.now()
        print(f"start_time is {start_time}")
        res = func(*args, **kwargs)
        end_time = datetime.datetime.now()
        print(f"end_time is {end_time}")
        last_time = end_time - start_time
        print(f"last_time is {last_time}")
        return res

    return wrapper


class AsyncDf:
    """
    针对dataframe的异步请求封装
    """

    def __init__(self, df: pd.DataFrame, df_response: str, df_request_name: List[str],
                 sema: int = 30, **kwargs):
        """
        df: 请求的df, 最后保存结果的 df
        df_request_name: 请求列的列名称 对应 curl -D 中需要格式化的字符串, 需要uuid的用户需要在df中自行构建
        df_response: 保存在df的响应列的列名称
        sema: 协程数目
        **kwargs : aiohttp.ClientSession().request中的参数
        """
        self.data = kwargs["data"]
        self.df_response = df_response
        self.sema = asyncio.BoundedSemaphore(sema)
        self.df = df
        self.df_request_name = df_request_name
        self.kwargs = kwargs
        self.url = self.kwargs["url"]
        self.method = self.kwargs["method"]
        # 下面参数在kwargs中移除
        self.remove_kwargs()

    def remove_kwargs(self):
        # data在 aiohttp.ClientSession().request 中是变化的
        self.kwargs.pop("data")
        # url,method在 aiohttp.ClientSession().request 中是固定参数
        self.kwargs.pop("url")
        self.kwargs.pop("method")
        # 下面参数 aiohttp.ClientSession().request 中没法识别
        self.kwargs.pop("verify")
        self.kwargs.pop("auth")
        self.kwargs.pop("cookies")

    @logger.catch()
    async def _process_url(self, ind_query: Tuple) -> None:
        """
        :type ind_query: 元组，第一个为index，第二个为需要格式化的内容，
        """
        ind, rows = ind_query
        content = tuple(rows[self.df_request_name].tolist())
        data = self.data % content
        async with self.sema:
            async with aiohttp.ClientSession() as session:
                resp = await session.request(self.method, self.url, data=data, **self.kwargs)
                await asyncio.sleep(0.5)
                self.df.loc[ind, self.df_response] = await resp.text()

    async def _gather_data(self):
        await asyncio.gather(
            *[self._process_url((ind, row)) for ind, row in self.df.iterrows()])

    @run_time_wraps
    def run(self) -> pd.DataFrame:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._gather_data())
        loop.close()
        return self.df

    def __call__(self):
        # 是否pre_process, post_process
        return self.run()

    @classmethod
    def from_curl(cls, df, curl_cmd, df_response, df_request_name, sema=30):
        """
        inputs: POSTMAN - curl
        """
        import uncurl
        curl_cmd = curl_cmd.replace(" -L", "")
        curl_cmd = curl_cmd.replace("--data-raw", "-d")
        context = uncurl.parse_context(curl_cmd)
        context_kwargs = context._asdict()
        return AsyncDf(df=df, df_response=df_response, df_request_name=df_request_name, sema=sema, **context_kwargs)

    def pre_process(self):
        return self.df

    def post_process(self):
        return self.df


if __name__ == '__main__':
    # rand_num = np.random.randint(500, size=(10000, 3))
    # df = pd.DataFrame(rand_num)
    # df.columns = ["user1", "user2", "user3"]
    # df_request_name = ["user1", "user2"]
    df = pd.read_csv("")
    df = df.drop_duplicates("query")
    logger.info(f'{df.len = }')
    curl_cmd = """
    curl -L -X POST 'https://fanyi.baidu.com/langdetect' \
    -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0' \
    -H 'Accept: */*' \
    -H 'Accept-Language: en-US,en;q=0.5' \
    -H 'Accept-Encoding: gzip, deflate, br' \
    -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
    -H 'X-Requested-With: XMLHttpRequest' \
    -H 'Origin: https://fanyi.baidu.com' \
    -H 'Connection: keep-alive' \
    -H 'Referer: https://fanyi.baidu.com/' \
    -H 'Sec-Fetch-Dest: empty' \
    -H 'Sec-Fetch-Mode: cors' \
    -H 'Sec-Fetch-Site: same-origin' \
    -H 'Cookie: BAIDUID=5205CCF1BE28D5ECBFA955B10D527899:FG=1' \
    --data-raw 'query=%s'
    """
    #
    async_df = AsyncDf.from_curl(df, curl_cmd, "baidu_langs", df_request_name=["query"], sema=20)
    df = async_df()
    df.to_csv("baidu_lang.csv",index=False)