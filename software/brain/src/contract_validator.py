"""
Contract Validator for HexForge PLA

Validates all JSON messages against contract schemas to enforce safety bounds
and protocol compliance.
"""

import json
import logging
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    raise ImportError("jsonschema library required. Install with: pip install jsonschema")

logger = logging.getLogger('hexforge.brain.contracts')

# Path to contract schemas (relative to this file)
CONTRACTS_DIR = Path(__file__).parent.parent.parent.parent / 'contracts' / 'schemas'


class ContractValidator:
    """Validates JSON messages against HexForge PLA contract schemas."""
    
    def __init__(self):
        """Load all contract schemas on initialization."""
        self.schemas = {}
        self._load_schemas()
    
    def _load_schemas(self):
        """Load all JSON schemas from contracts directory."""
        schema_files = {
            # PLA-specific contracts
            'action_proposal': 'action_proposal.schema.json',
            'action_decision': 'action_decision.schema.json',
            'action_execute': 'action_execute.schema.json',
            'session_log': 'session_log.schema.json',
            'device_status': 'device_status.schema.json',
            # HexForge global contracts
            'job_status': 'job_status.schema.json',
            'job_manifest': 'job_manifest.schema.json'
        }
        
        for name, filename in schema_files.items():
            schema_path = CONTRACTS_DIR / filename
            try:
                with open(schema_path, 'r') as f:
                    self.schemas[name] = json.load(f)
                logger.info(f"Loaded contract schema: {name}")
            except FileNotFoundError:
                logger.error(f"Contract schema not found: {schema_path}")
                raise
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in schema {filename}: {e}")
                raise
    
    def validate_proposal(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate action proposal against schema.
        
        Args:
            data: Proposal data to validate
            
        Returns:
            (is_valid, error_message)
        """
        return self._validate_against_schema(data, 'action_proposal')
    
    def validate_decision(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate action decision against schema.
        
        Args:
            data: Decision data to validate
            
        Returns:
            (is_valid, error_message)
        """
        return self._validate_against_schema(data, 'action_decision')
    
    def validate_execute(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate action execute command against schema.
        
        Args:
            data: Execute command to validate
            
        Returns:
            (is_valid, error_message)
        """
        return self._validate_against_schema(data, 'action_execute')
    
    def validate_session_log(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate session log entry against schema.
        
        Args:
            data: Log entry to validate
            
        Returns:
            (is_valid, error_message)
        """
        return self._validate_against_schema(data, 'session_log')
    
    def validate_device_status(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate device status report against schema.
        
        Args:
            data: Status report to validate
            
        Returns:
            (is_valid, error_message)
        """
        return self._validate_against_schema(data, 'device_status')
    
    def validate_job_status(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate HexForge job status (global contract).
        
        Args:
            data: Job status data to validate
            
        Returns:
            (is_valid, error_message)
        """
        return self._validate_against_schema(data, 'job_status')
    
    def validate_job_manifest(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate HexForge job manifest (global contract).
        
        Args:
            data: Job manifest data to validate
            
        Returns:
            (is_valid, error_message)
        """
        return self._validate_against_schema(data, 'job_manifest')
    
    def _validate_against_schema(
        self, 
        data: Dict[str, Any], 
        schema_name: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate data against named schema.
        
        Args:
            data: Data to validate
            schema_name: Name of schema to validate against
            
        Returns:
            (is_valid, error_message)
        """
        if schema_name not in self.schemas:
            error = f"Unknown schema: {schema_name}"
            logger.error(error)
            return False, error
        
        try:
            validate(instance=data, schema=self.schemas[schema_name])
            logger.debug(f"Validation passed for schema: {schema_name}")
            return True, None
        except ValidationError as e:
            error_msg = f"Validation failed for {schema_name}: {e.message}"
            logger.warning(error_msg)
            logger.debug(f"Validation path: {list(e.path)}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error validating {schema_name}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


# Global validator instance (singleton pattern)
_validator_instance: Optional[ContractValidator] = None


def get_validator() -> ContractValidator:
    """Get or create the global ContractValidator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = ContractValidator()
    return _validator_instance


# Convenience functions for direct validation
def validate_proposal(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate action proposal. Returns (is_valid, error_message)."""
    return get_validator().validate_proposal(data)


def validate_decision(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate action decision. Returns (is_valid, error_message)."""
    return get_validator().validate_decision(data)


def validate_execute(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate action execute command. Returns (is_valid, error_message)."""
    return get_validator().validate_execute(data)


def validate_session_log(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate session log entry. Returns (is_valid, error_message)."""
    return get_validator().validate_session_log(data)


def validate_job_status(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate HexForge job status (global contract). Returns (is_valid, error_message)."""
    return get_validator().validate_job_status(data)


def validate_job_manifest(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate HexForge job manifest (global contract). Returns (is_valid, error_message)."""
    return get_validator().validate_job_manifest(data)



def validate_device_status(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate device status report. Returns (is_valid, error_message)."""
    return get_validator().validate_device_status(data)
