def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    """計算 BMI (身高單位: 公分, 體重單位: 公斤)"""
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)


def get_bmi_category(bmi: float) -> str:
    """根據衛福部標準判斷 BMI 體位區間"""
    if bmi < 18.5:
        return "體重過輕 (Underweight)"
    elif 18.5 <= bmi < 24:
        return "正常範圍 (Normal)"
    elif 24 <= bmi < 27:
        return "過重 (Overweight)"
    elif 27 <= bmi < 30:
        return "輕度肥胖 (Mild obesity)"
    elif 30 <= bmi < 35:
        return "中度肥胖 (Moderate obesity)"
    else:
        return "重度肥胖 (Severe obesity)"


def main():
    print("=== BMI 計算器 (BMI Calculator) ===")
    try:
        height = float(input("請輸入身高 (cm): "))
        weight = float(input("請輸入體重 (kg): "))

        if height <= 0 or weight <= 0:
            print("❌ 身高與體重必須大於 0！")
            return

        bmi = calculate_bmi(height, weight)
        category = get_bmi_category(bmi)

        print(f"\n👉 您的 BMI 值為: {bmi:.2f}")
        print(f"👉 體位判定: {category}")

    except ValueError:
        print("❌ 輸入無效，請輸入數字符合格式。")


if __name__ == "__main__":
    main()
