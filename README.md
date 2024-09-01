# getSlackConvData
slackのトーク履歴・メンバーリストなどを簡易的に取得するツール
利用するにはslackのトークンが必要ですので、適宜アプリを用意してください。

# 機能概要

このプログラムでは、slackの指定したチャネルのメンバーリストと、トーク履歴を取得し、excelでエクスポートします。

トーク履歴はチャネル内に投稿されたメッセージと、スレッド内に投稿されたメッセージ両方を取得します。
全てのスレッド無いメッセージを取得する場合かなりのapiリクエストが発生するため、取得期間を制限することができるようになっています。


# how to use

1. このリポジトリをcloneする
2. `python -m venv venv`で仮想環境を作る
3. `. ./venv/bin/activate`で仮想に入る
4. `pip install --upgrade pip`
5. `pip install -r requirements.txt`
6. `python main.py`を実行するといくつかのディレクトリが生成される
7. `input` ディレクトリ内にinput.csvとtoken.csvを用意する。
8. `python main.py`を実行する


## input.csvについて

'id', 'requestDateRange'の2列を用意します。

* id:チャネルのidの文字列
* requestDateRange:スレッドメッセージの取得対象とする期間(整数)

### requestDateRangeについて

例えば、requestDateRangeに10を設定した場合、
10日以内のメッセージに対してのみスレッド内メッセージを取得します。