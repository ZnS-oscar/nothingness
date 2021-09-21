from predict import Predictor
import requests
import json
import time
import sys
import re

max_retry_times = 10
request_timeout = 60


class Client:
    def __init__(self) -> None:
        self.session = requests.session()

        source = self._get("https://ua.scu.edu.cn/login").text
        self.data_execution = re.findall(
            r'input name="execution" value="(.*?)"/>', source
        )[0]
        self.captcha_id = re.findall(
            r"config.captcha\s*=\s*{\s*type:\s*'image',\s*id:\s*'(\d+)'\s*}", source
        )[0]

    def _get(
        self, url: str, timeout: int = request_timeout, wait_time: int = 5
    ) -> requests.Response:
        response: requests.Response
        for i in range(max_retry_times):
            try:
                response = self.session.get(url, timeout=timeout)
            except:
                time.sleep(wait_time)
                if i + 1 == max_retry_times:
                    raise Exception("Max retries exceeded.")

        return response

    def _post(
        self, url: str, data: dict, timeout: int = request_timeout, wait_time: int = 5
    ) -> requests.Response:
        response: requests.Response
        for i in range(max_retry_times):
            try:
                response = self._post(url, data, timeout=timeout)
            except:
                time.sleep(wait_time)
                if i + 1 == max_retry_times:
                    raise Exception("Max retries exceeded.")

        return response

    def get_captcha(self) -> bytes:
        return self._get(
            "https://ua.scu.edu.cn/captcha?captchaId=" + self.captcha_id
        ).content

    def login(self, username: str, password: str, captcha: str) -> bool:
        response = self._post(
            "https://ua.scu.edu.cn/login",
            {
                "username": username,
                "password": password,
                "captcha": captcha,
                "submit": "LOGIN",
                "type": "username_password",
                "execution": self.data_execution,
                "_eventId": "submit",
            },
        )

        return response.status_code == 200

    def submit(self) -> None:
        source = self._get("https://wfw.scu.edu.cn/ncov/wap/default/index").text
        if "oldInfo" not in source:
            raise Exception("oldInfo not found!")

        old_info = json.loads(re.findall(r"oldInfo: ({.*?}),\n", source)[0])
        new_info = old_info
        new_info["created"] = round(time.time())

        response = self._post("https://wfw.scu.edu.cn/ncov/wap/default/save", new_info)
        result_json = json.loads(response.text)
        if result_json["e"] != 0:
            raise Exception("failed to submit!")


def main():
    client = Client()
    predictor = Predictor()
    username = sys.argv[1]
    password = sys.argv[2]
    for i in range(max_retry_times):
        captcha_bytes = client.get_captcha()
        captcha_prediction = predictor.predict(captcha_bytes)
        if client.login(username, password, captcha_prediction):
            break
        elif i + 1 == max_retry_times:
            exit(1)
    client.submit()


if __name__ == "__main__":
    main()
