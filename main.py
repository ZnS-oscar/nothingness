from predict import Predictor
import requests
import logging
import pickle
import base64
import copy
import json
import time
import sys
import re
import os

max_login_retry_times = 20
max_connection_retry_times = 10
request_timeout = 60
request_retry_wait_time = 5
login_retry_wait_time = 5
cookies_file_name = "cookies"

logging.basicConfig(level=logging.INFO)


class Client:
    def __init__(self) -> None:
        self._session = requests.Session()
        self._data_execution = ""
        self._captcha_id = ""
        self._predictor = Predictor()

    def _get(
        self,
        url: str,
        timeout: int = request_timeout,
        wait_time: int = request_retry_wait_time,
    ) -> requests.Response:
        response: requests.Response
        for i in range(max_connection_retry_times):
            try:
                response = self._session.get(url, timeout=timeout)
                break
            except:
                logging.warning(f"GET '{url}' failed, waiting for {wait_time} seconds")
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
                response = self._session.post(url, data=data, timeout=timeout)
                break
            except:
                logging.warning(f"POST '{url}' failed, waiting for {wait_time} seconds")
                time.sleep(wait_time)
                if i + 1 == max_connection_retry_times:
                    raise Exception("Max retries exceeded.")
                logging.info("retrying...")

        return response

    def _prepare(self) -> None:
        """
        prepare for username and password login
        not needed when login with cookie
        """
        logging.info("getting data_execution and captcha_id")
        source = self._get("https://ua.scu.edu.cn/login").text
        self._data_execution = re.findall(
            r'input name="execution" value="(.*?)"/>', source
        )[0]
        self._captcha_id = re.findall(
            r"config.captcha\s*=\s*{\s*type:\s*'image',\s*id:\s*'(\d+)'\s*}", source
        )[0]
        logging.info("got data_execution and captcha_id.")

    def _get_captcha(self) -> bytes:
        return self._get(
            "https://ua.scu.edu.cn/captcha?captchaId=" + self._captcha_id
        ).content

    def _login(self, username: str, password: str, captcha: str) -> bool:
        response = self._post(
            "https://ua.scu.edu.cn/login",
            {
                "username": username,
                "password": password,
                "captcha": captcha,
                "submit": "LOGIN",
                "type": "username_password",
                "execution": self._data_execution,
                "_eventId": "submit",
            },
        )

        return response.status_code == 200

    def login_with_credentials(self, username: str, password: str) -> None:
        self._prepare()
        for i in range(max_login_retry_times):
            logging.info("getting captcha")
            captcha_bytes = self._get_captcha()
            captcha_prediction = self._predictor.predict(captcha_bytes)
            logging.info(f"the captcha might be: {captcha_prediction}, logging in")
            # need to wait for a few seconds for the server to update catpcha info, I think.
            time.sleep(2)

            if self._login(username, password, captcha_prediction):
                logging.info("successfully logged in")
                break
            elif i + 1 == max_login_retry_times:
                raise Exception("max retries exceed when trying to login")

            logging.warning("wrong credentials or captcha, retrying...")
            time.sleep(login_retry_wait_time)

    def get_old_info(self) -> dict:
        """
        if not logged in, return empty dict
        if logged in, but oldInfo not in source, then something must be wrong, raise exception
        if everything seems to be right, then return oldInfo
        """
        logging.info("getting oldInfo")
        response = self._get("https://wfw.scu.edu.cn/ncov/wap/default/index")
        # if not logged in or cookie expired
        # server redirects you to https://ua.scu.edu.cn
        if response.url.startswith("https://ua.scu.edu.cn"):
            return dict()
        elif "oldInfo" not in response.text:
            raise Exception("oldInfo not found!")

        return json.loads(re.findall(r"oldInfo: ({.*?}),\n", response.text)[0])

    @staticmethod
    def update_info(old_info: dict) -> dict:
        """
        update old info, current just update the create time.
        """
        # deepcopy isn't necessary for this usecase, but I'ma use it anyway.
        new_info = copy.deepcopy(old_info)
        new_info["created"] = round(time.time())
        return new_info

    def submit(self, info: dict) -> None:
        logging.info("submitting")

        result_json = self._post(
            "https://wfw.scu.edu.cn/ncov/wap/default/save", info
        ).json()
        if result_json["e"] not in [0, 1]:
            raise Exception(f"failed to submit! server returned: {result_json}")

    def get_cookies(self) -> str:
        """
        return cookies as base64 encoded pickle encoded requests CookieJar
        """
        return base64.b64encode(pickle.dumps(self._session.cookies)).decode()

    def set_cookies(self, encoded_cookies: str) -> None:
        """
        the reverse of get_cookies
        """
        self._session.cookies.update(
            pickle.loads(base64.b64decode(encoded_cookies.encode()))
        )


def main():
    client = Client()
    _, username, password = sys.argv

    old_info = dict()
    if os.path.exists(cookies_file_name):
        logging.info("cookies file exists, trying to login with cookie")
        with open(cookies_file_name, "r") as f:
            client.set_cookies(f.read())
        old_info = client.get_old_info()

    # if no cookies or cookies expired
    if not old_info:
        logging.info(
            "no cookies file/cookies invalid or expired, fallback to login with credentials"
        )
        client.login_with_credentials(username, password)
        old_info = client.get_old_info()

    new_info = client.update_info(old_info)
    client.submit(new_info)

    with open(cookies_file_name, "w") as f:
        f.write(client.get_cookies())


if __name__ == "__main__":
    main()
