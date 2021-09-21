from predict import Predictor
import requests
import logging
import json
import time
import sys
import re

max_login_retry_times = 20
max_connection_retry_times = 10
request_timeout = 60
request_retry_wait_time = 5
login_retry_wait_time = 5


logging.basicConfig(level=logging.INFO)


class Client:
    def __init__(self) -> None:
        self.session = requests.session()

        logging.info("getting data_execution and captcha_id")
        source = self._get("https://ua.scu.edu.cn/login").text
        self.data_execution = re.findall(
            r'input name="execution" value="(.*?)"/>', source
        )[0]
        self.captcha_id = re.findall(
            r"config.captcha\s*=\s*{\s*type:\s*'image',\s*id:\s*'(\d+)'\s*}", source
        )[0]
        logging.info("got data_execution and captcha_id.")

    def _get(
        self,
        url: str,
        timeout: int = request_timeout,
        wait_time: int = request_retry_wait_time,
    ) -> requests.Response:
        response: requests.Response
        for i in range(max_connection_retry_times):
            try:
                response = self.session.get(url, timeout=timeout)
                break
            except:
                logging.warning(f"GET {url} failed, waiting for {wait_time} seconds")
                time.sleep(wait_time)
                if i + 1 == max_connection_retry_times:
                    raise Exception("Max retries exceeded.")
                logging.info("retrying...")

        return response

    def _post(
        self,
        url: str,
        data: dict,
        timeout: int = request_timeout,
        wait_time: int = request_retry_wait_time,
    ) -> requests.Response:
        response: requests.Response
        for i in range(max_connection_retry_times):
            try:
                response = self.session.post(url, data=data, timeout=timeout)
                break
            except:
                logging.warning(f"POST {url} failed, waiting for {wait_time} seconds")
                time.sleep(wait_time)
                if i + 1 == max_connection_retry_times:
                    raise Exception("Max retries exceeded.")
                logging.info("retrying...")

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
        logging.info("getting oldInfo")
        source = self._get("https://wfw.scu.edu.cn/ncov/wap/default/index").text
        if "oldInfo" not in source:
            raise Exception("oldInfo not found!")

        old_info = json.loads(re.findall(r"oldInfo: ({.*?}),\n", source)[0])
        new_info = old_info
        new_info["created"] = round(time.time())

        logging.info("submitting")

        response = self._post("https://wfw.scu.edu.cn/ncov/wap/default/save", new_info)
        result_json = json.loads(response.text)
        if result_json["e"] != 0:
            raise Exception("failed to submit!")


def main():
    client = Client()
    predictor = Predictor()
    username = sys.argv[1]
    password = sys.argv[2]
    for i in range(max_login_retry_times):
        logging.info("getting captcha")
        captcha_bytes = client.get_captcha()
        captcha_prediction = predictor.predict(captcha_bytes)
        logging.info(f"the captcha might be: {captcha_prediction}, logging in")
        # need to wait for a few seconds for the server to update catpcha info, I think.
        time.sleep(2)

        if client.login(username, password, captcha_prediction):
            logging.info("successfully logged in")
            break
        elif i + 1 == max_login_retry_times:
            raise Exception("max retries exceed when trying to login")

        logging.warning("wrong credentials or captcha, retrying...")
        time.sleep(login_retry_wait_time)

    client.submit()


if __name__ == "__main__":
    main()
