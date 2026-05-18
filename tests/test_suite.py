#!/usr/bin/env python3
"""Suite de validación integrada: importaciones, métodos y conservación física."""

import sys
import numpy as np

sys.path.insert(0, '.')

from src.model.particula import Particula
from src.model.motor_fisico import MotorFisico
from src.model.contenedor import Contenedor
from src.controller import Simulador
from src.view.visualizador import Visualizador


class TestRunner:
    """Ejecuta suite de pruebas validando leyes de conservación."""
    
    def __init__(self) -> None:
        self.tests_pasados = 0
        self.tests_totales = 0
    
    def _assert_approx(self, valor: float, esperado: float, tol: float = 1e-6) -> bool:
        """Compara valores con tolerancia."""
        return abs(valor - esperado) < tol
    
    def test_energia_cinetica(self) -> bool:
        """Valida cálculo de energía cinética."""
        p = Particula(0, np.array([0, 0]), np.array([3, 4]), 2.0, 0.5)
        ek = p.calcular_energia_cinetica()
        esperado = 0.5 * 2.0 * (3**2 + 4**2)
        return self._assert_approx(ek, esperado)
    
    def test_cantidad_movimiento(self) -> bool:
        """Valida cálculo de cantidad de movimiento."""
        p = Particula(0, np.array([0, 0]), np.array([2, 3]), 1.5, 0.5)
        p_vec = p.calcular_cantidad_movimiento()
        esperado = np.array([3.0, 4.5])
        return np.allclose(p_vec, esperado)
    
    def test_actualizacion_posicion(self) -> bool:
        """Valida cinemática: x = x + v*dt."""
        p = Particula(0, np.array([1.0, 2.0]), np.array([10.0, 20.0]), 1.0, 0.5)
        p.actualizar_posicion(0.1)
        esperado = np.array([2.0, 4.0])
        return np.allclose(p.posicion, esperado)
    
    def test_deteccion_colision_cercanas(self) -> bool:
        """Detecta colisión entre partículas cercanas."""
        p1 = Particula(0, np.array([0, 0]), np.array([0, 0]), 1.0, 1.0)
        p2 = Particula(1, np.array([1.5, 0]), np.array([0, 0]), 1.0, 1.0)
        return MotorFisico.detectar_colision(p1, p2)
    
    def test_deteccion_no_colision_lejanas(self) -> bool:
        """No detecta colisión entre partículas lejanas."""
        p1 = Particula(0, np.array([0, 0]), np.array([0, 0]), 1.0, 0.5)
        p2 = Particula(1, np.array([10, 10]), np.array([0, 0]), 1.0, 0.5)
        return not MotorFisico.detectar_colision(p1, p2)
    
    def test_conservacion_momento_elastica(self) -> bool:
        """Verifica conservación de momento en colisión elástica."""
        p1 = Particula(0, np.array([0, 0]), np.array([3, 0]), 1.0, 0.5, coef_restitution=1.0)
        p2 = Particula(1, np.array([2, 0]), np.array([-2, 0]), 1.0, 0.5, coef_restitution=1.0)
        
        p_inicial = p1.calcular_cantidad_movimiento() + p2.calcular_cantidad_movimiento()
        
        MotorFisico.resolver_colision(p1, p2)
        
        p_final = p1.calcular_cantidad_movimiento() + p2.calcular_cantidad_movimiento()
        
        return np.allclose(p_inicial, p_final, atol=1e-6)
    
    def test_conservacion_energia_elastica(self) -> bool:
        """Verifica conservación de energía en colisión elástica."""
        p1 = Particula(0, np.array([0, 0]), np.array([3, 0]), 1.0, 0.5, coef_restitution=1.0)
        p2 = Particula(1, np.array([2, 0]), np.array([-2, 0]), 1.0, 0.5, coef_restitution=1.0)
        
        ek_inicial = p1.calcular_energia_cinetica() + p2.calcular_energia_cinetica()
        
        MotorFisico.resolver_colision(p1, p2)
        
        ek_final = p1.calcular_energia_cinetica() + p2.calcular_energia_cinetica()
        
        return self._assert_approx(ek_inicial, ek_final, tol=0.01)
    
    def test_disipacion_energia_inelastica(self) -> bool:
        """Verifica disipación de energía en colisión inelástica."""
        p1 = Particula(0, np.array([0, 0]), np.array([3, 0]), 1.0, 0.5, coef_restitution=0.5)
        p2 = Particula(1, np.array([2, 0]), np.array([-2, 0]), 1.0, 0.5, coef_restitution=0.5)
        
        ek_inicial = p1.calcular_energia_cinetica() + p2.calcular_energia_cinetica()
        
        MotorFisico.resolver_colision(p1, p2)
        
        ek_final = p1.calcular_energia_cinetica() + p2.calcular_energia_cinetica()
        
        return ek_final < ek_inicial
    
    def test_deteccion_frontera(self) -> bool:
        """Detecta colisión con frontera."""
        contenedor = Contenedor(10, 10)
        p = Particula(0, np.array([0.3, 5]), np.array([0, 0]), 1.0, 0.5)
        return contenedor.detectar_colision_frontera(p)
    
    def run_all(self) -> None:
        """Ejecuta todos los tests."""
        print("\n" + "="*70)
        print("🔍 SUITE DE VALIDACIÓN INTEGRADA")
        print("="*70 + "\n")
        
        tests = [
            ("Energía cinética", self.test_energia_cinetica),
            ("Cantidad de movimiento", self.test_cantidad_movimiento),
            ("Actualización de posición", self.test_actualizacion_posicion),
            ("Detección de colisión (cercanas)", self.test_deteccion_colision_cercanas),
            ("No detección de colisión (lejanas)", self.test_deteccion_no_colision_lejanas),
            ("Conservación de momento (elástica)", self.test_conservacion_momento_elastica),
            ("Conservación de energía (elástica)", self.test_conservacion_energia_elastica),
            ("Disipación de energía (inelástica)", self.test_disipacion_energia_inelastica),
            ("Detección de frontera", self.test_deteccion_frontera),
        ]
        
        for nombre, test_func in tests:
            self.tests_totales += 1
            resultado = test_func()
            estado = "✓" if resultado else "✗"
            print(f"  {estado} {nombre}")
            if resultado:
                self.tests_pasados += 1
        
        print("\n" + "="*70)
        print(f"Resultado: {self.tests_pasados}/{self.tests_totales} tests pasaron")
        print("="*70 + "\n")
        
        if self.tests_pasados == self.tests_totales:
            print("✅ TODAS LAS PRUEBAS EXITOSAS\n")
            return True
        else:
            print(f"❌ {self.tests_totales - self.tests_pasados} PRUEBAS FALLARON\n")
            return False


if __name__ == '__main__':
    runner = TestRunner()
    success = runner.run_all()
    sys.exit(0 if success else 1)
