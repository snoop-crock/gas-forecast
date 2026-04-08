import numpy as np
import pandas as pd
from datetime import datetime

from .pvt import PVT
from .inflow import Inflow
from .hydraulics import Hydraulics
from .dcs import DKS
from .material_balance import MaterialBalance
from .water_influx import WaterInflux

# Параметры по умолчанию
default_params = {
    'start_year': 2025,
    'T_max': 60,
    'Q_polka': 0,
    'plateau_mode': 'auto',
    'target_recovery_rate': 1.5,
    'P_pl': 25,
    'T_pl': 80,
    'G_nach': 100,
    'rho_otn': 0.6,
    'N_skv': 10,
    'H_skv': 2500,
    'd_NKT': 100,
    'a_coef': 0.15,
    'b_coef': 0.0003,
    'dP_max': 10,
    'K_eks': 0.9,
    'DKS_mode': 'расчетный',
    'P_vh_DKS': 5,
    'P_vyh_DKS': 7.5,
    'N_DKS': 50,
    'VGF_nach': 0,
    'dVGF_dG': 10,
    'VGF_krit': 200,
    'opt_water': 1,
    'opt_friction': 1,
    'pvt_method': 'latonov'
}


def find_optimal_recovery_rate(params, max_years=30):
    """Поиск максимального темпа отбора для максимально длинной полки"""
    G_nach = params['G_nach'] * 1e9
    P_pl_init = params['P_pl']
    T_pl = params['T_pl'] + 273.15
    rho_otn = params['rho_otn']
    N_skv = params['N_skv']
    K_eks = params['K_eks']
    a_coef = params['a_coef']
    b_coef = params['b_coef']
    dP_max = params['dP_max']
    opt_water = params.get('opt_water', 1)
    VGF_nach = params.get('VGF_nach', 0)
    dVGF_dG = params.get('dVGF_dG', 10)
    VGF_krit = params.get('VGF_krit', 200)

    best_rate = 1  # минимальный темп 1%
    best_years = 0

    for rate in range(1, 21):
        polka_year = (rate / 100) * (G_nach / 1e9)
        polka_monthly = polka_year / 12

        Q_cum = 0
        P_pl_curr = P_pl_init
        VGF = VGF_nach
        years_on_plateau = 0

        for year in range(1, max_years + 1):
            year_ok = True
            for month in range(1, 13):
                days = 30

                if Q_cum > 0:
                    P_pl_curr = MaterialBalance.pressure_from_cumulative(
                        P_pl_init, T_pl, rho_otn, G_nach, Q_cum
                    )

                if P_pl_curr < 0.5:
                    year_ok = False
                    break

                P_zab_max = P_pl_curr - dP_max
                if P_zab_max < 0.5:
                    P_zab_max = 0.5

                Q_skv_day = Inflow.Q_gas(P_pl_curr, P_zab_max, a_coef, b_coef)

                if opt_water == 1 and VGF > 0:
                    krg = WaterInflux.rel_perm_gas(VGF, VGF_krit)
                    Q_skv_day *= krg

                Q_total_day = Q_skv_day * N_skv * K_eks
                Q_monthly = Q_total_day * days / 1e6

                if Q_monthly < polka_monthly * 0.98:
                    year_ok = False
                    break

                Q_cum += Q_monthly * 1e9

                if opt_water == 1:
                    VGF = WaterInflux.VGF_from_cumulative(
                        VGF_nach, dVGF_dG, Q_cum, G_nach, VGF_krit
                    )

            if year_ok:
                years_on_plateau = year
            else:
                break

        if years_on_plateau > best_years:
            best_years = years_on_plateau
            best_rate = rate

    return best_rate, best_years


def calculate_forecast(params):
    """Основная функция расчета прогноза"""

    # Извлечение параметров
    start_year = params['start_year']
    T_max = params['T_max']
    Q_polka_input = params['Q_polka']
    plateau_mode = params.get('plateau_mode', 'auto')
    target_recovery_rate = params.get('target_recovery_rate', 3)
    P_pl_init = params['P_pl']
    T_pl = params['T_pl'] + 273.15
    G_nach = params['G_nach'] * 1e9
    rho_otn = params['rho_otn']
    N_skv = params['N_skv']
    H_skv = params['H_skv']
    d_NKT = params['d_NKT']
    a_coef = params['a_coef']
    b_coef = params['b_coef']
    dP_max = params['dP_max']
    K_eks = params['K_eks']
    DKS_mode = params['DKS_mode']
    P_vh_DKS = params['P_vh_DKS']
    P_vyh_DKS = params['P_vyh_DKS']
    N_DKS_max = params['N_DKS']
    VGF_nach = params['VGF_nach']
    dVGF_dG = params['dVGF_dG']
    VGF_krit = params['VGF_krit']
    opt_friction = params['opt_friction']
    pvt_method = params['pvt_method']

    warning_message = None
    actual_recovery_rate = target_recovery_rate

    # Если режим "максимально длинная полка" — подбираем оптимальный темп
    if plateau_mode == 'auto':
        optimal_rate, optimal_years = find_optimal_recovery_rate(params, max_years=30)
        actual_recovery_rate = optimal_rate if optimal_rate > 0 else 1
        print(f"\n{'='*60}")
        print(f"🔍 ОПТИМАЛЬНЫЙ РЕЖИМ (максимально длинная полка):")
        print(f"   Оптимальный темп отбора: {actual_recovery_rate}% в год")
        print(f"   Ожидаемая длительность полки: {optimal_years} лет")
        print(f"   Рекомендуемая полка: {(actual_recovery_rate/100) * (params['G_nach']):.2f} млрд м³/год")
        print(f"{'='*60}\n")
        warning_message = f"✅ Оптимальный темп: {actual_recovery_rate}% (полка {optimal_years} лет)"
    else:
        sustainable_rate, sustainable_years = find_optimal_recovery_rate(params, max_years=5)
        if target_recovery_rate > sustainable_rate:
            print(f"\n{'='*60}")
            print(f"⚠️ ВНИМАНИЕ: Заданный темп {target_recovery_rate}% слишком высок")
            print(f"   Максимальный устойчивый темп: {sustainable_rate}%")
            print(f"   Полка продержится менее {sustainable_years} лет")
            print(f"{'='*60}\n")
            warning_message = f"⚠️ Темп {target_recovery_rate}% слишком высок! Максимум: {sustainable_rate}%"

    # Расчет максимального потенциала при начальных условиях
    P_zab_max_init = P_pl_init - dP_max
    if P_zab_max_init < 0.5:
        P_zab_max_init = 0.5
    Q_skv_init = Inflow.Q_gas(P_pl_init, P_zab_max_init, a_coef, b_coef)
    max_potential_rate = Q_skv_init * N_skv * K_eks * 365 / 1e6

    # Определяем полку
    if Q_polka_input == 0:
        Q_polka_year = (actual_recovery_rate / 100) * (G_nach / 1e9)
    else:
        Q_polka_year = Q_polka_input

    # Не можем превысить максимальный потенциал
    if Q_polka_year > max_potential_rate:
        print(f"⚠️ Полка {Q_polka_year:.2f} выше максимального потенциала {max_potential_rate:.2f}")
        Q_polka_year = max_potential_rate

    Q_polka_monthly = Q_polka_year / 12

    print(f"\n{'='*60}")
    print(f"📊 ПАРАМЕТРЫ РАСЧЕТА:")
    print(f"   Начальные запасы: {G_nach / 1e9:.0f} млрд м³")
    print(f"   Целевая полка: {Q_polka_year:.2f} млрд м³/год")
    print(f"   Максимальный потенциал: {max_potential_rate:.2f} млрд м³/год")
    print(f"{'='*60}\n")

    # Инициализация
    Q_cum = 0
    P_pl_curr = P_pl_init
    VGF = VGF_nach
    on_plateau = True
    prev_P_pl = P_pl_init 
    
    monthly_data = []
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    for i in range(T_max * 12):
        year = start_year + i // 12
        month = (i % 12) + 1
        days = days_in_month[month - 1]

        if month == 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
            days = 29

        # 1. Пластовое давление
        if Q_cum > 0:
            # Сохраняем предыдущее давление
            prev_P_pl = P_pl_curr
            
            # Расчет нового давления
            P_pl_curr = MaterialBalance.pressure_from_cumulative(
                P_pl_init, T_pl, rho_otn, G_nach, Q_cum
            )
            
            # Давление не может расти (физическое ограничение)
            if P_pl_curr > prev_P_pl and prev_P_pl > 0:
                P_pl_curr = prev_P_pl

        if P_pl_curr < 0.5:
            break

        # 2. Максимальный дебит (потенциал)
        P_zab_max = P_pl_curr - dP_max
        if P_zab_max < 0.5:
            P_zab_max = 0.5

        Q_skv_day_potential = Inflow.Q_gas(P_pl_curr, P_zab_max, a_coef, b_coef)

        # 3. Обводнение (корректировка потенциала)
        krg = WaterInflux.rel_perm_gas(VGF, VGF_krit)
        Q_skv_day_potential *= krg

        # 4. Суммарный потенциал
        Q_total_day_potential = Q_skv_day_potential * N_skv * K_eks
        Q_monthly_potential = Q_total_day_potential * days / 1e6

        # 5. Логика добычи
        if on_plateau:
            if Q_monthly_potential >= Q_polka_monthly:
                Q_monthly = Q_polka_monthly
                Q_total_day = Q_monthly * 1e6 / days
            else:
                Q_monthly = Q_monthly_potential
                Q_total_day = Q_total_day_potential
                on_plateau = False
                print(f"\n📉 СХОД С ПОЛКИ в {year}-{month:02d}")
                print(f"   Потенциал: {Q_monthly_potential*12:.2f} млрд м³/год")
                print(f"   Целевая полка: {Q_polka_year:.2f} млрд м³/год")
                print(f"   Накоплено: {Q_cum / 1e9:.1f} млрд м³\n")
        else:
            Q_monthly = Q_monthly_potential
            Q_total_day = Q_total_day_potential

        # 6. Устьевое давление
        if opt_friction == 1:
            P_u = Hydraulics.P_u_from_P_zab(
                P_zab_max, Q_total_day, H_skv, rho_otn, T_pl, d_NKT
            )
        else:
            P_u = P_zab_max - 0.001 * H_skv * rho_otn
            P_u = max(0.5, P_u)

        # 7. ДКС
        if DKS_mode == 'ограничительный':
            Q_max_DKS = DKS.Q_max_from_power(
                N_DKS_max, P_u, P_vyh_DKS, T_pl, rho_otn
            ) * 1e6
            if Q_max_DKS > 0 and Q_total_day > Q_max_DKS:
                Q_total_day = Q_max_DKS
                Q_monthly = Q_total_day * days / 1e6
            N_DKS = N_DKS_max
        else:
            N_DKS = DKS.power_calc(
                Q_total_day / 1e6, P_u, P_vyh_DKS, T_pl, rho_otn
            )

        # 8. Накопление
        Q_cum += Q_monthly * 1e9

        # 9. ВГФ (теперь всегда считается)
        VGF = WaterInflux.VGF_from_cumulative(
            VGF_nach, dVGF_dG, Q_cum, G_nach, VGF_krit
        )
        # Добыча воды (м³/мес)
        Q_water_m3 = Q_monthly * 1e9 * VGF / 1e6

        Q_water_thousand_m3 = Q_water_m3 / 1000

        current_recovery_rate = (Q_monthly * 12) / (G_nach / 1e9) * 100

        date = datetime(year, month, 1)
        monthly_data.append({
            'Дата': date,
            'Год': year,
            'Квартал': (month - 1) // 3 + 1,
            'Месяц': month,
            'P_пл, МПа': round(P_pl_curr, 2),
            'Добыча газа, млрд м³/мес': round(Q_monthly, 4),  # 4 знака для точности
            'Добыча газа, млрд м³/год': round(Q_monthly * 12, 2),
            'Накоплено, млрд м³': round(Q_cum / 1e9, 2),
            'Остаток, млрд м³': round((G_nach - Q_cum) / 1e9, 2),
            'Темп отбора, %': round(current_recovery_rate, 2),
            'P_у, МПа': round(P_u, 2),
            'P_заб, МПа': round(P_zab_max, 2),
            'ВГФ, г/м³': round(VGF, 1),
            'Добыча воды, тыс. м³/мес': round(Q_water_thousand_m3, 3),  # 6 знаков для маленьких значений
            'Мощность ДКС, МВт': round(N_DKS, 1),
            'На полке': 1 if on_plateau else 0,
            'Потенциал, млрд м³/мес': round(Q_monthly_potential, 4)
        })

        if month == 12:
            status = "✅ НА ПОЛКЕ" if on_plateau else "⬇️ ПАДЕНИЕ"
            print(f"Год {year}: добыча {Q_monthly * 12:.2f} млрд м³, темп {current_recovery_rate:.1f}%, {status}")

    monthly_df = pd.DataFrame(monthly_data)

    if len(monthly_df) == 0:
        return {'monthly_df': [], 'yearly_df': [], 'params': params, 'warning': warning_message}

    yearly_df = monthly_df.groupby('Год', as_index=False).agg({
        'Добыча газа, млрд м³/мес': 'sum',
        'Накоплено, млрд м³': 'last',
        'P_пл, МПа': 'mean',
        'Темп отбора, %': 'mean',
        'Мощность ДКС, МВт': 'mean',
        'На полке': 'max'
    })

    yearly_df.columns = ['Год', 'Добыча газа, млрд м³/год', 'Накоплено, млрд м³',
                         'Среднее P_пл, МПа', 'Средний темп отбора, %',
                         'Средняя мощность ДКС, МВт', 'На полке']

    # Округление годовых данных
    yearly_df['Добыча газа, млрд м³/год'] = yearly_df['Добыча газа, млрд м³/год'].round(3)
    yearly_df['Накоплено, млрд м³'] = yearly_df['Накоплено, млрд м³'].round(3)
    yearly_df['Среднее P_пл, МПа'] = yearly_df['Среднее P_пл, МПа'].round(3)
    yearly_df['Средний темп отбора, %'] = yearly_df['Средний темп отбора, %'].round(3)
    yearly_df['Средняя мощность ДКС, МВт'] = yearly_df['Средняя мощность ДКС, МВт'].round(3)
    yearly_df['На полке'] = yearly_df['На полке'].astype(int)

    # Принудительно преобразуем Год в int
    yearly_df['Год'] = yearly_df['Год'].astype(int)
    monthly_df['Год'] = monthly_df['Год'].astype(int)

    plateau_years = yearly_df[yearly_df['На полке'] == 1]['Год'].count()

    print(f"\n{'='*60}")
    print(f"📊 ИТОГИ РАСЧЕТА:")
    print(f"   Длительность полки: {plateau_years} лет")
    print(f"   Накопленная добыча: {Q_cum / 1e9:.1f} млрд м³")
    print(f"   Конечный КИГ: {min(100, Q_cum / G_nach * 100):.1f}%")
    print(f"{'='*60}\n")

    return {
        'monthly_df': monthly_df.to_dict('records'),
        'yearly_df': yearly_df.to_dict('records'),
        'params': params,
        'G_nach': G_nach / 1e9,
        'plateau_level': Q_polka_year,
        'plateau_years': plateau_years,
        'optimal_rate': actual_recovery_rate if plateau_mode == 'auto' else None,
        'warning': warning_message
    }