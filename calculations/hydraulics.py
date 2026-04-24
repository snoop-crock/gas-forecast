from .pvt import PVT


class Hydraulics:
    """Расчет гидравлики в стволе скважины"""

    @staticmethod
    def P_u_from_P_zab(P_zab, Q_th_m3day, H_m, rho_otn, T_K, d_NKT_mm=100):
        """
        Расчет устьевого давления по забойному (упрощенная формула)

        Параметры:
        ----------
        P_zab : float
            Забойное давление (МПа)
        Q_th_m3day : float
            Дебит (тыс.м³/сут)
        H_m : float
            Глубина скважины (м)
        rho_otn : float
            Относительная плотность газа
        T_K : float
            Температура (K)
        d_NKT_mm : float
            Диаметр НКТ (мм)

        Возвращает:
        -----------
        P_u : float
            Устьевое давление (МПа)
        """
        if Q_th_m3day <= 0:
            P_u = P_zab - 0.001 * H_m * rho_otn
            return max(0.1, P_u)

        # Среднее давление для оценки плотности
        P_sr = (P_zab + P_zab - 0.001 * H_m * rho_otn) / 2
        if P_sr < 0.1:
            P_sr = 0.5

        z_sr = PVT.z_factor(P_sr, T_K, rho_otn)
        rho_g = PVT.density(P_sr, T_K, rho_otn, z_sr)

        # Упрощенная формула с учетом трения
        lambda_coef = 0.02  # коэффициент гидравлического сопротивления
        d_NKT_m = d_NKT_mm / 1000

        term = 1.4e-8 * lambda_coef * rho_otn * \
            Q_th_m3day ** 2 * T_K * z_sr * H_m / d_NKT_m ** 5

        if P_zab ** 2 > term:
            P_u = np.sqrt(P_zab ** 2 - term)
        else:
            P_u = P_zab - 0.001 * H_m * rho_otn

        P_u = max(0.1, min(P_u, P_zab * 0.95))

        return P_u

    @staticmethod
    def choke_pressure_drop(P_u, Q_mm3day, D_choke_mm=8, C=0.85, rho_otn=0.6):
        """
        Расчет давления после штуцера
        
        Штуцер — это сужающее устройство на устье скважины.
        При стандартных размерах (6-12 мм) и рабочих дебитах 
        создается перепад 0.5-2 МПа.
        
        Упрощенная модель для газовых скважин:
        ΔP = k * Q² / D⁴
        
        где k — эмпирический коэффициент (для природного газа ≈ 0.0005)
        """
        if Q_mm3day <= 0 or D_choke_mm <= 0:
            return P_u
        
        # Эмпирическая формула перепада на штуцере
        k = 0.0005 / (C * C)  # коэффициент, учитывающий расход
        
        # Перевод диаметра в дюймы (для эмпирической формулы)
        D_inch = D_choke_mm / 25.4
        
        # Перепад давления (МПа)
        dP_choke = k * (Q_mm3day ** 2) / (D_inch ** 4) * rho_otn
        
        # Ограничиваем разумным диапазоном (0.1 - 3 МПа)
        dP_choke = max(0.1, min(3.0, dP_choke))
        
        P_after_choke = max(0.5, P_u - dP_choke)
        
        return P_after_choke