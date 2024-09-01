from datetime import datetime

class Logger:
    def __init__(self):
        self.last_action = None  # 直前に呼ばれたメソッドの名前を保持
        self.counter = 0  # 連続表示のカウンター

    def _reset_counter(self):
        """カウンターをリセットする。"""
        self.counter = 0

    def _check_line_break(self):
        """80回連続表示で改行を挿入。"""
        self.counter += 1
        if self.counter >= 80:
            print()  # 改行を挿入
            self._reset_counter()

    def view_message_access(self):
        """メッセージAPIアクセスの表示（>）"""
        print(">", end="", flush=True)
        self._check_line_break()
        self.last_action = 'message'

    def view_thread_access(self):
        """スレッドAPIアクセスの表示（-）"""
        print("-", end="", flush=True)
        self._check_line_break()
        self.last_action = 'thread'

    def view_email_api_access(self):
        """APIでメアド問い合わせを行った旨の表示（'/'）"""
        print("/", end="", flush=True)
        self._check_line_break()
        self.last_action = 'email_api'

    def view_api_result_waiting(self):
        print("|", end="", flush=True)
        self._check_line_break()

    def view_up_waiting_timer(self):
        print("↑", end="", flush=True)
        self._check_line_break()

    def view_down_waiting_timer(self):
        print("↓", end="", flush=True)
        self._check_line_break()

    def view_api_retry(self):
        """リトライ表示（x）"""
        print("x", end="", flush=True)
        self._check_line_break()
        self.last_action = 'retry'

    def view_log(self, message: str):
        """ログ表示機能"""
        # 直前にログ表示以外のアクションがあった場合、ログの表示前に改行を入れる
        if self.last_action in ['message', 'thread', 'retry', 'email_api', 'email_cache']:
            print()  # 改行を挿入

        # 現在時刻とメッセージを表示
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"{current_time} - {message}")

        # アクションをリセット
        self.last_action = 'log'
        self._reset_counter()
