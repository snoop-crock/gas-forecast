from calculations import calculate_forecast, default_params

# Тест ОБОИХ режимов
print("=" * 60)
print("РЕЖИМ ОГРАНИЧИТЕЛЬНЫЙ (новая логика)")
print("=" * 60)
params_restrictive = {**default_params, 'DKS_mode': 'ограничительный'}
result_r = calculate_forecast(params_restrictive)

if 'monthly_df' in result_r and len(result_r['monthly_df']) > 0:
    monthly_r = result_r['monthly_df']
    dks_values_r = [row.get('Мощность ДКС, МВт', 0) for row in monthly_r]
    dks_max_r = max(dks_values_r)
    dks_avg_plateau_r = sum(dks_values_r[-100:]) / 100 if len(dks_values_r) > 100 else 0
    
    print(f'Макс мощность: {dks_max_r:.2f} МВт')
    print(f'Ср. на конечной полке: {dks_avg_plateau_r:.2f} МВт')
    print(f'Характер кривой: {"ВЫПОЛАЖЕНА (плотина)" if abs(dks_max_r - dks_avg_plateau_r) < 2 else "ИМЕЕТ ПИК"}')
    
    # Покажем добычу
    prod_values_r = [row.get('Добыча газа, млрд м³/мес', 0) for row in monthly_r]
    prod_avg_plateau_r = sum(prod_values_r[-100:]) / 100 if len(prod_values_r) > 100 else 0
    print(f'Ср. добыча на полке: {prod_avg_plateau_r:.3f} млрд м³/мес')

print("\n" + "=" * 60)
print("РЕЖИМ РАСЧЕТНЫЙ (старая логика)")
print("=" * 60)
params_calc = {**default_params, 'DKS_mode': 'расчетный'}
result_c = calculate_forecast(params_calc)

if 'monthly_df' in result_c and len(result_c['monthly_df']) > 0:
    monthly_c = result_c['monthly_df']
    dks_values_c = [row.get('Мощность ДКС, МВт', 0) for row in monthly_c]
    dks_max_c = max(dks_values_c)
    dks_avg_plateau_c = sum(dks_values_c[-100:]) / 100 if len(dks_values_c) > 100 else 0
    
    print(f'Макс мощность: {dks_max_c:.2f} МВт')
    print(f'Ср. на конечной полке: {dks_avg_plateau_c:.2f} МВт')
    print(f'Характер кривой: {"ВЫПОЛАЖЕНА" if abs(dks_max_c - dks_avg_plateau_c) < 2 else "ИМЕЕТ ПИК"}')
    
    # Покажем добычу
    prod_values_c = [row.get('Добыча газа, млрд м³/мес', 0) for row in monthly_c]
    prod_avg_plateau_c = sum(prod_values_c[-100:]) / 100 if len(prod_values_c) > 100 else 0
    print(f'Ср. добыча на полке: {prod_avg_plateau_c:.3f} млрд м³/мес')

print("\n" + "=" * 60)
print("ВЫВОД: Выбирайте ОГРАНИЧИТЕЛЬНЫЙ режим для выполаживания мощности")
print("=" * 60)
