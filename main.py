from predict import Predictor
import requests
import json
import time
import sys
import re

max_retry_times = 10


class Client:
    def __init__(self) -> None:
        self.session = requests.session()

        source = self.session.get("https://ua.scu.edu.cn/login", timeout=60).text
        self.data_execution = re.findall(
            r'input name="execution" value="(.*?)"/>', source
        )[0]
        self.captcha_id = re.findall(
            r"config.captcha = {\n    type: \'image\',\n    id: \'(\d+)\'\n}", source
        )[0]

    def get_captcha(self) -> bytes:
        return self.session.get(
            "https://ua.scu.edu.cn/captcha?captchaId=" + self.captcha_id
        ).content

    def login(self, username: str, password: str, captcha: str):
        result = self.session.post(
            "https://ua.scu.edu.cn/login",
            data={
                "username": username,
                "password": password,
                "captcha": captcha,
                "submit": "LOGIN",
                "type": "username_password",
                "execution": self.data_execution,
                "_eventId": "submit",
            },
        )

        return result.status_code == 200

    def submit(self) -> None:
        source = self.session.get(
            "https://wfw.scu.edu.cn/ncov/wap/default/index", timeout=60
        ).text
        if "oldInfo" not in source:
            raise Exception("oldInfo not found!")

        old_info = json.loads(re.findall(r"oldInfo: ({.*?}),\n", source)[0])
        new_info = old_info
        new_info["created"] = round(time.time())

        result = self.session.post(
            "https://wfw.scu.edu.cn/ncov/wap/default/save", data=new_info, timeout=60
        )
        result_json = json.loads(result.text)
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
