import numpy as np


class WaterInflux:
    """Расчет обводнения"""

    @staticmethod
    def VGF_from_cumulative(VGF_init, dVGF_dG, Q_cum, G_nach, VGF_krit):
        """
        Расчет текущего водогазового фактора

        Параметры:
        ----------
        VGF_init : float
            Начальный водогазовый фактор (г/м³)
        dVGF_dG : float
            Интенсивность роста ВГФ на 10% отбора (г/м³)
        Q_cum : float
            Накопленная добыча (м³)
        G_nach : float
            Начальные запасы (м³)
        VGF_krit : float
            Критический ВГФ (г/м³)

        Возвращает:
        -----------
        VGF : float
            Текущий ВГФ (г/м³)
        """
        recovery = Q_cum / G_nach

        # Рост ВГФ пропорционально отбору
        VGF = VGF_init + recovery * dVGF_dG * 10

        return min(VGF, VGF_krit)

    @staticmethod
    def rel_perm_gas(VGF, VGF_krit):
        """
        Относительная фазовая проницаемость для газа при обводнении

        Возвращает коэффициент снижения дебита
        """
        if VGF <= 0:
            return 1.0

        krg = 1 - (VGF / VGF_krit) ** 0.5
        return max(0, krg)
