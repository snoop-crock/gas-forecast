from .pvt import PVT


class MaterialBalance:
    """Расчет материального баланса газовой залежи"""

    """
    Расчет текущего пластового давления по накопленной добыче

    Параметры:
    ----------
    P_pl_init : float
        Начальное пластовое давление (МПа)
    T_K : float
        Пластовая температура (K)
    rho_otn : float
        Относительная плотность газа
    G_nach : float
        Начальные геологические запасы (м³)
    Q_cum : float
        Накопленная добыча (м³)

    Возвращает:
    -----------
    P_pl : float
        Текущее пластовое давление (МПа)
    """
    @staticmethod
    def pressure_from_cumulative(P_pl_init, T_K, rho_otn, G_nach, Q_cum, prev_P_pl=None):
        if Q_cum <= 0:
            return P_pl_init

        z_init = PVT.z_factor(P_pl_init, T_K, rho_otn)
        Pz_init = P_pl_init / z_init

        # Начальное приближение — предыдущее давление или начальное
        if prev_P_pl is not None and prev_P_pl > 0:
            P_pl = prev_P_pl
        else:
            P_pl = P_pl_init

        for _ in range(20):
            z_curr = PVT.z_factor(P_pl, T_K, rho_otn)
            Pz_curr = P_pl / z_curr
            Pz_target = Pz_init * (1 - Q_cum / G_nach)

            if abs(Pz_curr - Pz_target) < 0.001:
                break

            # Корректировка с релаксацией (0.5 — скорость сходимости)
            new_P_pl = Pz_target * z_curr
            P_pl = 0.5 * P_pl + 0.5 * new_P_pl

        # Давление не может быть выше начального
        return max(0.1, min(P_pl, P_pl_init))
