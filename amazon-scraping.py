from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
# プロ用の待機モジュール
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import random

# --- 設定 ---
KEYWORD = "Python プログラミング"  # 検索したいキーワード
CSV_FILE_NAME = "amazon_products.csv"


def main():
    # --- Chromeオプション（人間らしく見せる設定） ---
    options = Options()
    # ヘッドレスモードはAmazonなどの場合、検知されやすいため今回は画面を表示させます
    # options.add_argument('--headless')
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
    options.add_argument('--disable-blink-features=AutomationControlled')  # 自動操作フラグを隠す

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # プロ用の待機設定（最大10秒待つインスタンスを作成）
    wait = WebDriverWait(driver, 10)

    try:
        # 1. Amazonトップページへ
        driver.get("https://www.amazon.co.jp/")

        # 検索窓を探して入力（id="twotabsearchtextbox" は比較的安定）
        # EC.presence_of_element_located で「要素が存在するまで待つ」を実現
        search_box = wait.until(EC.presence_of_element_located((By.ID, "twotabsearchtextbox")))
        search_box.send_keys(KEYWORD)
        search_box.submit()  # エンターキーを押すのと同じ

        print(f"検索完了: {KEYWORD}")
        time.sleep(random.uniform(2, 4))  # ページ遷移後のひと休み

        # 2. 商品リストの取得
        # Amazonの検索結果商品は data-component-type="s-search-result" という属性を持っています
        items = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")

        print(f"{len(items)} 件の商品が見つかりました。データ抽出を開始します。")

        results = []

        for item in items[:10]:  # テストのため上位10件のみ
            try:
                # --- 商品名の取得 ---
                # h2タグの中のspanなどを探す
                title_elm = item.find_element(By.CSS_SELECTOR, "h2 a span")
                title = title_elm.text

                # --- 価格の取得 ---
                # Amazonの価格は ".a-price-whole" (円の部分) というクラスがよく使われます
                # 価格がない商品（在庫切れなど）もあるため try-except で囲むのは必須
                try:
                    price_elm = item.find_element(By.CSS_SELECTOR, ".a-price-whole")
                    price = price_elm.text
                except:
                    price = "0"  # 取れない場合は0やNoneにする

                # --- URLの取得 ---
                link_elm = item.find_element(By.CSS_SELECTOR, "h2 a")
                url = link_elm.get_attribute("href")

                print(f"取得: {title[:20]}... / {price}円")

                results.append({
                    "title": title,
                    "price_raw": price,  # "2,500" のような文字列のまま
                    "url": url
                })

            except Exception as e:
                print(f"要素取得エラー（スキップします）: {e}")
                continue

        # 3. データ整形と保存
        df = pd.DataFrame(results)

        # 【データサイエンティストの仕事】
        # "2,500" などの文字列を、計算可能な数値 2500 に変換する処理
        # replaceでカンマを除去し、int型に変換する
        df['price'] = df['price_raw'].astype(str).str.replace(',', '').astype(int)

        df.to_csv(CSV_FILE_NAME, index=False, encoding="utf-8-sig")
        print("完了しました")

    except Exception as e:
        print(f"全体エラー: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()