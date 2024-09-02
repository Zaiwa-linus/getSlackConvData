from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import time
import pandas as pd
from datetime import datetime, timedelta 
import logger
import threading


class SlackManager:
    def __init__(self, user_cache, max_retries=5, timeout=60, retry_interval=20):
        """
        SlackManagerクラスの初期化メソッド。
        UserCacheインスタンスを受け取り、内部のプロパティとして保持します。
        Slackトークンはファイルから読み込み、WebClient を初期化します。

        :param user_cache: UserCacheインスタンス
        :param max_retries: 最大リトライ回数
        :param timeout: タイムアウト時間（秒）
        :param retry_interval: リトライ間隔（秒）
        """
        self.user_cache = user_cache
        self.client = WebClient(token=self.read_credential())
        self.max_retries = max_retries
        self.timeout = timeout
        self.retry_interval = retry_interval
        self.rate_limit_wait_time = 0  # レート制限による追加待機時間
        self.logger = logger.Logger()
        self.consecutive_success_count = 0  # 連続でレート制限に達しなかった回数をインスタンス変数として初期化

    def retry_request(self, func, default_wait_time=0, *args, **kwargs):
        """
        リトライ処理を共通化したメソッド。指定された関数をリトライ回数に基づいて実行する。

        :param func: 実行する関数
        :param default_wait_time: デフォルトの待ち時間（秒）
        :param args: 関数に渡す引数
        :param kwargs: 関数に渡すキーワード引数
        :return: 関数の実行結果
        """
        error_messages = []  # エラーメッセージをストックするリスト
        

        # タイムアウト待機のアラートを表示する関数
        def start_waiting_timer():
            self.logger.view_api_result_waiting()
            # タイマーを10秒ごとに再設定
            self.waiting_timer = threading.Timer(10, start_waiting_timer)
            self.waiting_timer.start()

        for attempt in range(1, self.max_retries + 1):
            # タイマーを開始
            self.waiting_timer = threading.Timer(10, start_waiting_timer)
            self.waiting_timer.start()

            try:
                self.client.timeout = self.timeout * attempt
                time.sleep(default_wait_time+self.rate_limit_wait_time)

                result = func(*args, **kwargs)
                self.waiting_timer.cancel()  # 応答があればタイマーをキャンセル
                self.consecutive_success_count += 1

                # 100回連続で成功した場合、待ち時間を減少
                if self.consecutive_success_count >= 50:
                    self.rate_limit_wait_time = self.rate_limit_wait_time - 0.01
                    self.logger.view_down_waiting_timer()  # 待ち時間を減らした場合のログ表示
                    self.consecutive_success_count = 0
                return result

            except SlackApiError as e:
                self.waiting_timer.cancel()  # エラーが発生した場合もタイマーをキャンセル
                error_messages.append(f"Error in {func.__name__}: {e.response['error']}")

                # レート制限に達した場合の処理
                if 'ratelimited' in e.response['error']:
                    self.rate_limit_wait_time += 0.03
                    self.logger.view_up_waiting_timer()  # 待ち時間を増やした場合のログ表示
                    self.consecutive_success_count = 0  # 成功カウンターをリセット

            except Exception as e:
                self.waiting_timer.cancel()
                error_messages.append(f"Unexpected error in {func.__name__}: {e}")

            # リトライの進行状況を表示
            self.logger.view_api_retry()
            time.sleep(self.retry_interval)

        # リトライが全て失敗した場合、エラーメッセージをまとめて表示
        self.logger.view_log(f"Failed to execute {func.__name__} after {self.max_retries} attempts.")
        for error_message in error_messages:
            self.logger.view_log(error_message)

        return None







    def fetch_conversations_history(self, channel_id, cursor=None):
        """
        Slack APIのconversations_historyメソッドをリトライ機能付きで呼び出す。

        :param channel_id: チャンネルID
        :param cursor: ページング用のカーソル
        :return: APIレスポンスデータ
        """
        return self.retry_request(func=self.client.conversations_history,default_wait_time=60/50,channel=channel_id, cursor=cursor, limit=1000)

    def fetch_conversations_replies(self, channel_id, thread_ts):
        """
        Slack APIのconversations_repliesメソッドをリトライ機能付きで呼び出す。

        :param channel_id: チャンネルID
        :param thread_ts: スレッドタイムスタンプ
        :return: APIレスポンスデータ
        """
        return self.retry_request(func=self.client.conversations_replies,default_wait_time=60/50, channel=channel_id, ts=thread_ts, limit=1000)

    def get_user_email(self, member_id):
        """
        指定されたメンバーIDのユーザー情報を取得し、メールアドレスを返すメソッド。
        キャッシュ内に存在する場合はキャッシュから返し、存在しない場合はAPIから取得してキャッシュに保存。

        :param member_id: SlackのメンバーID
        :return: メールアドレス、または "this account seems to be a bot"
        """
        # キャッシュ内のユーザーを確認
        cached_user = next((user for user in self.user_cache.valid_users if user['user_id'] == member_id), None)
        if cached_user:
            return cached_user['email']

        # APIから取得
        self.logger.view_email_api_access()  # メールアドレス問い合わせのためのAPIアクセスを表示
        response = self.retry_request(func=self.client.users_info,default_wait_time=60/100, user=member_id)
        if response:
            user_info = response['user']
            email = user_info.get('profile', {}).get('email')

            # メールアドレスをキャッシュに保存
            if email:
                self.user_cache.add_user(member_id, email)
            else:
                email = "this account seems to be a bot"
                self.user_cache.add_user(member_id, email)
            return email

        # 取得に失敗した場合も "this account seems to be a bot" として保存
        email = "this account seems to be a bot"
        self.user_cache.add_user(member_id, email)
        return email




    def read_credential(self, file_path='./input/token.csv'):
        """
        'creds.txt' ファイルの1行目を読み取り、返すメソッド。

        :param file_path: クレデンシャルを読み込むファイルのパス（デフォルトは 'creds.txt'）
        :return: ファイルの1行目の内容を文字列で返す
        """
        try:
            with open(file_path, 'r') as file:
                first_line = file.readline().strip()  # 1行目を読み取り、前後の空白や改行を削除
            return first_line
        except FileNotFoundError:
            self.logger.view_log(f"Error: The file {file_path} was not found.")
            return None
        except Exception as e:
            self.logger.view_log(f"An error occurred: {e}")
            return None

    def get_all_members(self, channel_id):
        """
        指定されたチャンネルの全メンバーIDを取得するメソッド。

        :param channel_id: チャンネルID
        :return: メンバーIDのリスト
        """
        members = []
        cursor = None  # ページング用のカーソル

        while True:
            try:
                # チャンネルの参加者リストを取得（ページング対応）
                response = self.client.conversations_members(channel=channel_id, cursor=cursor, limit=1000)
                members.extend(response['members'])  # メンバーIDをリストに追加

                # 次のページがあるかを確認
                cursor = response.get('response_metadata', {}).get('next_cursor', None)
                if not cursor:  # 次のページがなければ終了
                    break

            except SlackApiError as e:
                self.logger.view_log(f"Error fetching members: {e.response['error']}")
                break

        return members


    
    def get_all_user_info(self, channel_id: str):
        """
        チャネルの参加者情報を取得し、メールアドレスをつけて返す。
        戻り値はpandasのDataFrameとし、戻り値の列はchannel_id, export_date, member_id, emailとする。
        export_dateはyyyy-mm-ddの文字列形式とすること。

        :param channel_id: チャンネルID
        :return: DataFrame（列: channel_id, export_date, member_id, email）
        """
        # チャネルの参加者リストの取得を開始
        self.logger.view_log(f"Fetching user list for channel: {channel_id}")
        members = self.get_all_members(channel_id)
        self.logger.view_log(f"Total members to process: {len(members)}")

        export_date = datetime.now().strftime('%Y-%m-%d')
        data = []

        # 各メンバーのメールアドレスを取得
        for member_id in members:
            email = self.get_user_email(member_id)
            data.append({
                'channel_id': channel_id,
                'export_date': export_date,
                'member_id': member_id,
                'email': email
            })

        # DataFrameに変換
        df = pd.DataFrame(data, columns=['channel_id', 'export_date', 'member_id', 'email'])
        return df

        
    def get_all_messages(self, channel_id: str, get_thread_date_length=300):
        """
        チャネルのメッセージ一覧を取得し、スレッド内のメッセージも含める。
        メッセージはページごとにロードされ、各ページとスレッド内のデータのロード進捗をログに出力する。

        :param channel_id: チャンネルID
        :param get_thread_date_length: スレッドデータ取得の期間（日数）
        :return: DataFrame（カラム: type, user, team, text, ts, thread_ts, react, datetime, email, channel_id, export_date）
        """
        # チャネル名の取得
        channel_name = channel_id
        self.logger.view_log(f"Start fetching messages for channel '{channel_name}'")

        # メッセージの取得
        messages = self.fetch_channel_messages(channel_id)
        total_messages = len(messages)  # メッセージの総数をカウント
        self.logger.view_log(f"Total {total_messages} messages fetched for channel '{channel_name}'")

        data = []

        # 現在の日付からのスレッド取得期間の計算
        thread_cutoff_date = datetime.now() - timedelta(days=get_thread_date_length)

        # メインメッセージの取得
        for i, message in enumerate(messages, 1):
            # メッセージの日付を取得
            message_datetime = datetime.fromtimestamp(float(message['ts'])) if 'ts' in message else None

            # メッセージの処理
            self.process_message(data, message, channel_id)

            # messageのdatetimeが動作時の日付のget_thread_date_length日より前ならスレッド内のデータは取らない
            if message_datetime and message_datetime < thread_cutoff_date:
                ##self.logger.view_log(f"Skipping threads for message dated {message_datetime} in channel '{channel_name}' (older than {get_thread_date_length} days).")
                continue  # スレッドの取得をスキップ

            # スレッドメッセージの取得
            if 'thread_ts' in message and message['thread_ts'] == message['ts']:
                thread_ts = message['thread_ts']
                thread_messages = self.fetch_thread_messages(channel_id, thread_ts)

                for thread_message in thread_messages:
                    #self.logger.view_thread_access()  # 各スレッドメッセージの取得を示す
                    self.process_message(data, thread_message, channel_id, thread_ts)

        # DataFrameに変換
        df = pd.DataFrame(data, columns=['type', 'user', 'team', 'text', 'ts', 'thread_ts', 'react', 'datetime', 'email', 'channel_id', 'export_date'])
        self.logger.view_log(f"Finished fetching messages for channel '{channel_name}'")
        return df.drop_duplicates()

    def clean_string(self, value):
        """
        Excelで使用できない文字を除去する関数。

        :param value: 文字列
        :return: クリーンアップされた文字列
        """
        if isinstance(value, str):
            # Excelで使用できない特殊文字を除去
            return ''.join(c for c in value if c.isprintable())
        return value

    def process_message(self, data, message, channel_id, thread_ts=None):
        """
        メッセージデータを整形してリストに追加する。

        :param data: メッセージデータを格納するリスト
        :param message: メッセージデータ
        :param channel_id: チャンネルID
        :param thread_ts: スレッドタイムスタンプ（オプション）
        """
        user = message.get('user')
        email = self.get_user_email(user) if user else None
        reacts = str(message.get('reactions')) if 'reactions' in message else None  # リアクションを文字列に変換して保存

        data.append({
            'type': message.get('type'),
            'user': user,
            'team': message.get('team'),
            'text': self.clean_string(message.get('text')),  # 'text'のみクリーンアップ
            'ts': message.get('ts'),
            'thread_ts': thread_ts or message.get('thread_ts'),
            'react': reacts,
            'datetime': datetime.fromtimestamp(float(message.get('ts', 0))).strftime('%Y-%m-%d %H:%M:%S') if message.get('ts') else None,
            'email': email,
            'channel_id': channel_id,
            'export_date': datetime.now().strftime('%Y-%m-%d')
        })




    def fetch_channel_messages(self, channel_id: str):
        """
        指定されたチャネルのメインメッセージを全て取得する。
        各ページのロード時にログを出力。

        :param channel_id: チャンネルID
        :return: メッセージのリスト
        """
        messages = []
        cursor = None
        page = 1

        while True:
            self.logger.view_message_access()
            response = self.fetch_conversations_history(channel_id, cursor)
            if response is None:
                break
            messages.extend(response['messages'])

            # 次のページがあるかを確認
            cursor = response.get('response_metadata', {}).get('next_cursor', None)
            if not cursor:
                break

            page += 1

        return messages

    def fetch_thread_messages(self, channel_id: str, thread_ts: str):
        """
        スレッドの返信メッセージを全て取得する。
        各スレッド内データのロード時にログを出力。

        :param channel_id: チャンネルID
        :param thread_ts: スレッドタイムスタンプ
        :return: スレッドメッセージのリスト
        """
        thread_messages = []
        thread_cursor = None
        thread_page = 1

        while True:
            self.logger.view_thread_access()
            response = self.fetch_conversations_replies(channel_id, thread_ts)
            if response is None:
                break
            thread_messages.extend(response['messages'])

            # 次のページがあるかを確認
            thread_cursor = response.get('response_metadata', {}).get('next_cursor', None)
            if not thread_cursor:
                break

            thread_page += 1

        return thread_messages

    def convert_messages_to_react_data(self, messages_df):
        """
        get_all_messagesの応答から、リアクションデータを抽出して整形し、DataFrameとして返す。
        DataFrameはts, user, stamp, email, channel_id, export_dateをカラムに持つ。

        :param messages_df: get_all_messagesの応答として得られるDataFrame
        :return: リアクションデータを整形したDataFrame
        """
        react_data = []

        # 各メッセージのリアクションを抽出
        for index, row in messages_df.iterrows():
            ts = row['ts']
            channel_id = row['channel_id']
            export_date = row['export_date']

            # リアクションがある場合、個々のリアクションデータを抽出
            if row['react']:
                try:
                    # リアクションを文字列からリストに変換
                    reactions = eval(row['react'])
                    for reaction in reactions:
                        for user in reaction['users']:
                            # userのIDを使ってメールアドレスを取得
                            email = self.get_user_email(user)
                            react_data.append({
                                'ts': ts,
                                'user': user,
                                'stamp': reaction['name'],
                                'email': email,
                                'channel_id': channel_id,
                                'export_date': export_date
                            })
                except (SyntaxError, NameError, TypeError):
                    # リアクションデータのパースに失敗した場合の対処
                    self.logger.view_log(f"Failed to parse reactions for message {ts}")

        # DataFrameに変換
        df = pd.DataFrame(react_data, columns=['ts', 'user', 'stamp', 'email', 'channel_id', 'export_date'])
        return df.drop_duplicates()


    
    @staticmethod
    def linear_interpolation(start, end, step, total_steps):
        """
        線形補間を行うヘルパー関数。

        :param start: 開始値
        :param end: 終了値
        :param step: 現在のステップ
        :param total_steps: 全ステップ数
        :return: 補間された値
        """
        return start + (end - start) * (step / total_steps)



