from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import random

# --- 設定 ---
KEYWORD = "Python プログラミング"
CSV_FILE_NAME = "amazon_products.csv"


def main():
    options = Options()
    # options.add_argument('--headless')
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
    options.add_argument('--disable-blink-features=AutomationControlled')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 10)

    try:
        driver.get("https://www.amazon.co.jp/")
        search_box = wait.until(EC.presence_of_element_located((By.ID, "twotabsearchtextbox")))
        search_box.send_keys(KEYWORD)
        search_box.submit()

        print(f"検索完了: {KEYWORD}")
        time.sleep(random.uniform(2, 4))

        # 抽出対象を取得
        items = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
        print(f"{len(items)} 件の商品が見つかりました。上位9件のデータ抽出を開始します。")

        results = []

        for i, item in enumerate(items[:9]):
            try:
                title = "取得失敗"
                url = ""
                price = "0"

                try:
                    # 1. まずタイトル(h2)を特定する
                    # data-cy='title-recipe' があればそこから、なければ全体から探す
                    try:
                        title_section = item.find_element(By.CSS_SELECTOR, "[data-cy='title-recipe']")
                        h2 = title_section.find_element(By.TAG_NAME, "h2")
                    except:
                        h2 = item.find_element(By.TAG_NAME, "h2")

                    title = h2.text

                    # 2. そのh2に関連するリンクだけを探す
                    # パターンA: リンクの中にh2がある (<a> <h2>...</h2> </a>)
                    # パターンB: h2の中にリンクがある (<h2> <a>...</a> </h2>)
                    try:
                        # パターンAチェック（h2の親要素がaタグか？）
                        parent = h2.find_element(By.XPATH, "./..")
                        if parent.tag_name == "a":
                            url = parent.get_attribute("href")
                        else:
                            # パターンBチェック（h2の中にaタグがあるか？）
                            child_link = h2.find_element(By.TAG_NAME, "a")
                            url = child_link.get_attribute("href")
                    except:
                        # 万が一どちらでも取れなかった場合の最終手段
                        # item全体から "a-link-normal" クラスを持つ最初のリンクを探す
                        link_elm = item.find_element(By.CSS_SELECTOR, "a.a-link-normal")
                        url = link_elm.get_attribute("href")

                except Exception as e:
                    print(f"No.{i + 1} タイトル/URL取得失敗: {e}")
                    # URLが取れないと意味がないのでスキップするか、空文字で進める
                    pass

                #価格の取得
                try:
                    price_elm = item.find_element(By.CSS_SELECTOR, ".a-price-whole")
                    price = price_elm.text
                except:
                    price = "0"

                print(f"No.{i + 1} 取得: {title[:15]}... / {price}円")

                results.append({
                    "title": title,
                    "price_raw": price,
                    "url": url
                })

            except Exception as e:
                print(f"No.{i + 1} スキップ: {e}")
                continue

        # 保存処理
        if not results:
            print("データなし")
        else:
            df = pd.DataFrame(results)
            df['price'] = df['price_raw'].astype(str).str.replace(',', '').astype(int)
            df.to_csv(CSV_FILE_NAME, index=False, encoding="utf-8-sig")
            print(f"完了: {CSV_FILE_NAME}")

    except Exception as e:
        print(f"全体エラー: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
