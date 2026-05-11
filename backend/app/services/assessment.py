"""
健康评估算法服务
包含 BMI、BMR、TDEE、每日摄入量、目标预测日期的计算逻辑
"""
import math
from datetime import datetime, timedelta, timezone
from app.schemas.schemas import GoalEnum, ExerciseFrequencyEnum, GenderEnum


# 活动系数映射
ACTIVITY_MULTIPLIERS = {
    ExerciseFrequencyEnum.never: 1.2,
    ExerciseFrequencyEnum.one_two: 1.375,
    ExerciseFrequencyEnum.three_five: 1.55,
    ExerciseFrequencyEnum.daily: 1.725,
}

# 目标调整系数
GOAL_CALORIE_ADJUSTMENT = {
    GoalEnum.lose_weight: -500,     # 每日减少 500 kcal
    GoalEnum.gain_muscle: 300,      # 每日增加 300 kcal
    GoalEnum.maintain: 0,           # 维持
    GoalEnum.improve_endurance: -200,  # 适度减少
}

# 安全的每周体重变化量（kg）
WEEKLY_CHANGE = {
    GoalEnum.lose_weight: -0.5,
    GoalEnum.gain_muscle: 0.25,
    GoalEnum.maintain: 0,
    GoalEnum.improve_endurance: -0.25,
}


def calculate_bmi(weight_kg: float, height_cm: float) -> tuple[float, str]:
    """计算 BMI 及其分类"""
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    bmi = round(bmi, 2)

    if bmi < 18.5:
        category = "underweight"
    elif bmi < 24:
        category = "normal"
    elif bmi < 28:
        category = "overweight"
    else:
        category = "obese"

    return bmi, category


def calculate_bmr(
    weight_kg: float, height_cm: float, age: int, gender: str
) -> float:
    """使用 Mifflin-St Jeor 公式计算基础代谢率"""
    if gender == GenderEnum.male:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return round(bmr, 1)


def calculate_tdee(bmr: float, exercise_frequency: str) -> float:
    """根据活动系数计算每日总能量消耗"""
    multiplier = ACTIVITY_MULTIPLIERS.get(exercise_frequency, 1.2)
    return round(bmr * multiplier, 1)


def calculate_daily_intake(tdee: float, goal: str) -> int:
    """根据目标计算建议每日摄入量"""
    adjustment = GOAL_CALORIE_ADJUSTMENT.get(goal, 0)
    intake = tdee + adjustment
    return max(1200, round(intake))  # 最低 1200 kcal 安全底线


def calculate_prediction_days(
    current_weight: float, target_weight: float, goal: str
) -> int | None:
    """计算目标预测天数"""
    weekly_change = WEEKLY_CHANGE.get(goal, 0)
    if weekly_change == 0:
        return None  # 维持目标无需预测

    diff = abs(target_weight - current_weight)
    if diff < 0.1:
        return 0  # 已达到目标

    weeks = diff / abs(weekly_change)
    days = math.ceil(weeks * 7)
    return days


def calculate_macros(daily_calories: int, goal: str) -> tuple[float, float, float]:
    """计算宏量营养素分解（蛋白质/碳水/脂肪，单位 g）"""
    if goal == GoalEnum.gain_muscle:
        protein_ratio, carbs_ratio, fat_ratio = 0.30, 0.45, 0.25
    elif goal == GoalEnum.lose_weight:
        protein_ratio, carbs_ratio, fat_ratio = 0.35, 0.35, 0.30
    else:
        protein_ratio, carbs_ratio, fat_ratio = 0.25, 0.50, 0.25

    protein_g = round(daily_calories * protein_ratio / 4, 1)  # 4 kcal/g
    carbs_g = round(daily_calories * carbs_ratio / 4, 1)      # 4 kcal/g
    fat_g = round(daily_calories * fat_ratio / 9, 1)          # 9 kcal/g

    return protein_g, carbs_g, fat_g


def run_full_assessment(
    gender: str,
    goal: str,
    age: int,
    height_cm: float,
    weight_kg: float,
    target_weight_kg: float,
    exercise_frequency: str,
) -> dict:
    """执行完整的健康评估，返回所有计算结果"""
    bmi, bmi_category = calculate_bmi(weight_kg, height_cm)
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    tdee = calculate_tdee(bmr, exercise_frequency)
    daily_intake = calculate_daily_intake(tdee, goal)
    prediction_days = calculate_prediction_days(weight_kg, target_weight_kg, goal)
    protein_g, carbs_g, fat_g = calculate_macros(daily_intake, goal)
    weekly_change = WEEKLY_CHANGE.get(goal, 0)

    return {
        "bmi_value": bmi,
        "bmi_category": bmi_category,
        "bmr": bmr,
        "tdee": tdee,
        "daily_calorie_intake": daily_intake,
        "target_prediction_days": prediction_days,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "weekly_weight_change_kg": weekly_change,
    }
