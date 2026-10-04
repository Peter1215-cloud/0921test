def jpy_to_twd(jpy: float, rate: float = 0.21) -> float:
    """將日圓 (JPY) 依照指定匯率換算為新台幣 (TWD)"""
    return jpy * rate


def main():
    print("=" * 40)
    print("      日幣換算台幣計算器 (JPY to TWD)")
    print("=" * 40)

    # 預設參考匯率 (1 JPY ≈ 0.21 TWD)
    default_rate = 0.21

    try:
        # 輸入日幣金額
        jpy_input = input("請輸入日幣金額 (JPY): ").strip()
        jpy = float(jpy_input)

        if jpy < 0:
            print("❌ 金額不能為負數！")
            return

        # 匯率輸入（可直接 Enter 使用預設）
        rate_input = input(f"請輸入匯率 [直接按 Enter 使用預設 {default_rate}]: ").strip()
        rate = float(rate_input) if rate_input else default_rate

        if rate <= 0:
            print("❌ 匯率必須大於 0！")
            return

        # 計算結果
        twd = jpy_to_twd(jpy, rate)

        print("\n" + "-" * 40)
        print(f"💴 日幣金額: {jpy:,.2f} JPY")
        print(f"📊 使用匯率: 1 JPY = {rate} TWD")
        print(f"🇹🇼 換算台幣: 約 {twd:,.2f} TWD (四捨五入: 約 {round(twd):,} 元)")
        print("-" * 40)

    except ValueError:
        print("❌ 輸入無效，請輸入有效數字！")


if __name__ == "__main__":
    main()
