"""
Unit tests for thermodynamic module.
"""

import pytest
import numpy as np
import warnings
from thermodynamic import (
    thermodynamic_entropy, 
    thermodynamic_entropy_from_temperature,
    validate_thermodynamic_parameters,
    ThermodynamicSystem
)


class TestThermodynamicEntropy:
    """Test thermodynamic entropy calculations."""
    
    def test_basic_calculation(self):
        """Test basic thermodynamic entropy calculation."""
        work = 10.0
        free_energy_change = 5.0
        gamma = 1.0
        
        result = thermodynamic_entropy(work, free_energy_change, gamma)
        expected = gamma * (work - free_energy_change)  # 1.0 * (10.0 - 5.0) = 5.0
        
        assert result == expected
    
    def test_gamma_scaling(self):
        """Test gamma parameter scaling."""
        work = 10.0
        free_energy_change = 5.0
        
        # Test different gamma values
        for gamma in [0.5, 1.0, 2.0, 10.0]:
            result = thermodynamic_entropy(work, free_energy_change, gamma)
            expected = gamma * (work - free_energy_change)
            assert result == expected
    
    def test_array_inputs(self):
        """Test with array inputs."""
        work = np.array([10.0, 15.0, 20.0])
        free_energy_change = np.array([5.0, 10.0, 12.0])
        gamma = 1.0
        
        result = thermodynamic_entropy(work, free_energy_change, gamma)
        expected = np.array([5.0, 5.0, 8.0])
        
        np.testing.assert_array_equal(result, expected)
    
    def test_zero_gamma(self):
        """Test with gamma = 0."""
        work = 100.0
        free_energy_change = 50.0
        gamma = 0.0
        
        result = thermodynamic_entropy(work, free_energy_change, gamma)
        assert result == 0.0
    
    def test_negative_entropy(self):
        """Test case resulting in negative entropy."""
        work = 5.0
        free_energy_change = 10.0  # ΔF > W
        gamma = 1.0
        
        result = thermodynamic_entropy(work, free_energy_change, gamma)
        expected = 1.0 * (5.0 - 10.0)  # -5.0
        
        assert result == expected
    
    def test_invalid_gamma_negative(self):
        """Test invalid negative gamma."""
        with pytest.raises(ValueError, match="gamma must be non-negative"):
            thermodynamic_entropy(10.0, 5.0, gamma=-1.0)
    
    def test_invalid_gamma_type(self):
        """Test invalid gamma type."""
        with pytest.raises(TypeError, match="gamma must be a numeric value"):
            thermodynamic_entropy(10.0, 5.0, gamma="invalid")
    
    def test_shape_mismatch(self):
        """Test shape mismatch in arrays."""
        work = np.array([1.0, 2.0])
        free_energy_change = np.array([1.0])  # Different shape
        
        with pytest.raises(ValueError, match="must have same shape"):
            thermodynamic_entropy(work, free_energy_change)
    
    def test_nan_inputs(self):
        """Test NaN inputs."""
        with pytest.raises(ValueError, match="contain NaN values"):
            thermodynamic_entropy(np.nan, 5.0)
        
        with pytest.raises(ValueError, match="contain NaN values"):
            thermodynamic_entropy(10.0, np.nan)
    
    def test_infinite_inputs(self):
        """Test infinite inputs."""
        with pytest.raises(ValueError, match="contain infinite values"):
            thermodynamic_entropy(np.inf, 5.0)
        
        with pytest.raises(ValueError, match="contain infinite values"):
            thermodynamic_entropy(10.0, -np.inf)


class TestThermodynamicEntropyFromTemperature:
    """Test temperature-based entropy calculation."""
    
    def test_basic_temperature_calculation(self):
        """Test basic temperature calculation."""
        temperature = 300.0  # Kelvin
        entropy_change = 0.1  # J/K
        gamma = 1.0
        
        result = thermodynamic_entropy_from_temperature(temperature, entropy_change, gamma)
        expected = gamma * temperature * entropy_change  # 1.0 * 300.0 * 0.1 = 30.0
        
        assert result == expected
    
    def test_zero_temperature(self):
        """Test zero temperature (should raise error)."""
        with pytest.raises(ValueError, match="Temperature must be positive"):
            thermodynamic_entropy_from_temperature(0.0, 0.1)
    
    def test_negative_temperature(self):
        """Test negative temperature (should raise error)."""
        with pytest.raises(ValueError, match="Temperature must be positive"):
            thermodynamic_entropy_from_temperature(-100.0, 0.1)


class TestValidateParameters:
    """Test parameter validation."""
    
    def test_valid_parameters(self):
        """Test with valid parameters."""
        assert validate_thermodynamic_parameters(10.0, 5.0, 1.0) is True
    
    def test_second_law_warning(self):
        """Test second law violation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # This should trigger warning: W + ΔF < 0
            validate_thermodynamic_parameters(5.0, -10.0, 1.0)
            
            assert len(w) == 1
            assert "second law" in str(w[0].message).lower()
    
    def test_invalid_types(self):
        """Test invalid parameter types."""
        with pytest.raises(TypeError, match="All parameters must be numeric"):
            validate_thermodynamic_parameters("invalid", 5.0, 1.0)
    
    def test_nan_parameters(self):
        """Test NaN parameters."""
        with pytest.raises(ValueError, match="contain NaN values"):
            validate_thermodynamic_parameters(np.nan, 5.0, 1.0)
    
    def test_infinite_parameters(self):
        """Test infinite parameters."""
        with pytest.raises(ValueError, match="contain infinite values"):
            validate_thermodynamic_parameters(np.inf, 5.0, 1.0)


class TestThermodynamicSystem:
    """Test ThermodynamicSystem class."""
    
    def test_system_initialization(self):
        """Test system initialization."""
        system = ThermodynamicSystem(gamma=2.0)
        assert system.gamma == 2.0
        assert system.work_history == []
        assert system.free_energy_history == []
    
    def test_add_process(self):
        """Test adding a process."""
        system = ThermodynamicSystem()
        
        entropy = system.add_process(work=10.0, free_energy_change=5.0)
        assert entropy == 5.0
        assert system.work_history == [10.0]
        assert system.free_energy_history == [5.0]
    
    def test_multiple_processes(self):
        """Test adding multiple processes."""
        system = ThermodynamicSystem(gamma=1.0)
        
        processes = [
            (10.0, 5.0),  # entropy = 5.0
            (15.0, 10.0), # entropy = 5.0
            (20.0, 12.0)  # entropy = 8.0
        ]
        
        for work, free_energy in processes:
            system.add_process(work, free_energy)
        
        assert len(system.work_history) == 3
        assert system.total_entropy() == 5.0 + 5.0 + 8.0
    
    def test_reset_system(self):
        """Test resetting system."""
        system = ThermodynamicSystem()
        system.add_process(10.0, 5.0)
        
        assert len(system.work_history) == 1
        
        system.reset()
        
        assert system.work_history == []
        assert system.free_energy_history == []
        assert system.total_entropy() == 0.0
    
    def test_string_representation(self):
        """Test string representation."""
        system = ThermodynamicSystem(gamma=1.5)
        
        empty_str = str(system)
        assert "ThermodynamicSystem" in empty_str
        assert "gamma=1.5" in empty_str
        assert "processes=0" in empty_str
        
        system.add_process(10.0, 5.0)
        
        populated_str = str(system)
        assert "processes=1" in populated_str
    
    def test_empty_system_total_entropy(self):
        """Test total entropy of empty system."""
        system = ThermodynamicSystem()
        assert system.total_entropy() == 0.0
    
    def test_invalid_process_addition(self):
        """Test adding invalid process."""
        system = ThermodynamicSystem(gamma=-1.0)  # Invalid gamma
        
        with pytest.raises(ValueError, match="gamma must be non-negative"):
            system.add_process(10.0, 5.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])