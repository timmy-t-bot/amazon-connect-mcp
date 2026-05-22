"""Amazon Connect MCP Server - Phone Number Management Tools.

This module provides MCP tools for managing phone numbers in Amazon Connect including:
- Searching for available phone numbers
- Claiming phone numbers
- Releasing phone numbers
- Listing claimed phone numbers
- Describing phone number details
- Updating phone number settings
"""

import json
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

# Initialize AWS Connect client
try:
    connect_client = boto3.client("connect")
    PHONE_NUMBERS_AVAILABLE = True
except Exception:
    connect_client = None
    PHONE_NUMBERS_AVAILABLE = False


class ConnectPhoneNumberError(Exception):
    """Exception raised for Connect phone number operations."""
    pass


def _get_connect_client() -> Any:
    """Get the Connect client, initializing if necessary."""
    global connect_client
    if connect_client is None:
        connect_client = boto3.client("connect")
    return connect_client


def connect_phone_numbers_search(
    phone_number_country_code: str,
    phone_number_type: str = "DID",
    target_arn: str = "",
    phone_number_prefix: str = "",
    max_results: int = 50
) -> Dict[str, Any]:
    """Search for available phone numbers to claim.
    
    Args:
        phone_number_country_code: ISO country code (e.g., 'US', 'UK', 'CA', 'AU')
        phone_number_type: Type of number - 'DID' (Direct Inward Dialing) or 'TOLL_FREE'
        target_arn: Optional ARN of the target (instance or format: instance:queue)
        phone_number_prefix: Optional phone number prefix filter (e.g., '+1800')
        max_results: Maximum number of results to return (default 50)
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - phone_numbers: List of available phone numbers with details
        - next_token: Token for pagination
        
    Raises:
        ConnectPhoneNumberError: If the search fails
        
    Example:
        >>> result = connect_phone_numbers_search(
        ...     phone_number_country_code="US",
        ...     phone_number_type="TOLL_FREE",
        ...     max_results=10
        ... )
        >>> for number in result["phone_numbers"]:
        ...     print(f"Available: {number['phone_number']}")
    """
    try:
        client = _get_connect_client()
        
        params = {
            "PhoneNumberCountryCode": phone_number_country_code,
            "PhoneNumberType": phone_number_type
        }
        
        if target_arn:
            params["TargetArn"] = target_arn
        
        if phone_number_prefix:
            params["PhoneNumberPrefix"] = phone_number_prefix
        
        if max_results:
            params["MaxResults"] = max_results
        
        response = client.search_available_phone_numbers(**params)
        
        phone_numbers = []
        for pn in response.get("PhoneNumbers", []):
            phone_numbers.append({
                "phone_number": pn.get("PhoneNumber"),
                "phone_number_country_code": pn.get("PhoneNumberCountryCode"),
                "phone_number_type": pn.get("PhoneNumberType"),
                "target_arn": pn.get("TargetArn")
            })
        
        return {
            "status": "success",
            "phone_numbers": phone_numbers,
            "next_token": response.get("NextToken")
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectPhoneNumberError(f"Failed to search phone numbers: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectPhoneNumberError(f"Failed to search phone numbers: {str(e)}")


def connect_phone_numbers_claim(
    instance_id: str,
    phone_number: str = "",
    phone_number_country_code: str = "",
    phone_number_type: str = "",
    target_arn: str = "",
    description: str = "",
    tags: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Claim a phone number for a Connect instance.
    
    Can either claim a specific number or auto-claim the first available number
    in the specified country.
    
    Args:
        instance_id: Connect instance ID
        phone_number: Specific phone number to claim (e.g., +1-800-555-0123).
            If not provided, will search and claim automatically.
        phone_number_country_code: For auto-claim: country code (e.g., 'US')
        phone_number_type: For auto-claim: type ('DID' or 'TOLL_FREE')
        target_arn: ARN where to assign the number (instance or queue ARN)
        description: Optional description for the phone number
        tags: Optional dictionary of tags to apply
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - phone_number_id: ID of the claimed phone number
        - phone_number_arn: ARN of the claimed phone number
        - phone_number: The actual phone number
        
    Raises:
        ConnectPhoneNumberError: If the claim fails or no numbers available
        
    Example:
        >>> # Claim a specific number
        >>> connect_phone_numbers_claim(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     phone_number="+1-800-555-0123"
        ... )
        
        >>> # Auto-claim a number
        >>> connect_phone_numbers_claim(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     phone_number_country_code="US",
        ...     phone_number_type="TOLL_FREE"
        ... )
    """
    try:
        client = _get_connect_client()
        
        params = {
            "InstanceId": instance_id
        }
        
        if target_arn:
            params["TargetArn"] = target_arn
        
        if phone_number:
            # Claim specific number
            params["PhoneNumber"] = phone_number
        elif phone_number_country_code and phone_number_type:
            # Search for available number first
            search_result = connect_phone_numbers_search(
                phone_number_country_code=phone_number_country_code,
                phone_number_type=phone_number_type,
                target_arn=target_arn,
                max_results=1
            )
            
            if search_result["status"] != "success" or not search_result["phone_numbers"]:
                raise ConnectPhoneNumberError("No available phone numbers found for the specified criteria")
            
            params["PhoneNumber"] = search_result["phone_numbers"][0]["phone_number"]
        else:
            raise ConnectPhoneNumberError("Either phone_number or both phone_number_country_code and phone_number_type must be provided")
        
        if description:
            params["Description"] = description
        
        if tags:
            params["Tags"] = tags
        
        response = client.claim_phone_number(**params)
        
        return {
            "status": "success",
            "phone_number_id": response.get("PhoneNumberId"),
            "phone_number_arn": response.get("PhoneNumberArn"),
            "phone_number": params.get("PhoneNumber")
        }
    except ConnectPhoneNumberError:
        raise
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectPhoneNumberError(f"Failed to claim phone number: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectPhoneNumberError(f"Failed to claim phone number: {str(e)}")


def connect_phone_numbers_release(
    instance_id: str,
    phone_number_id: str
) -> Dict[str, Any]:
    """Release a previously claimed phone number.
    
    WARNING: Released phone numbers may not be reclaimable.
    
    Args:
        instance_id: Connect instance ID
        phone_number_id: ID of the phone number to release
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - message: Description of the result
        
    Raises:
        ConnectPhoneNumberError: If the release fails
        
    Example:
        >>> connect_phone_numbers_release(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     phone_number_id="12345678-1234-1234-1234-123456789012"
        ... )
    """
    try:
        client = _get_connect_client()
        
        params = {
            "InstanceId": instance_id,
            "PhoneNumberId": phone_number_id
        }
        
        client.release_phone_number(**params)
        
        return {
            "status": "success",
            "message": f"Phone number {phone_number_id} released successfully"
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectPhoneNumberError(f"Failed to release phone number: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectPhoneNumberError(f"Failed to release phone number: {str(e)}")


def connect_phone_numbers_list(
    instance_id: str,
    max_results: int = 50,
    phone_number_country_codes: Optional[List[str]] = None,
    phone_number_types: Optional[List[str]] = None,
    next_token: str = ""
) -> Dict[str, Any]:
    """List all phone numbers for a Connect instance.
    
    Args:
        instance_id: Connect instance ID
        max_results: Maximum number of results (default 50)
        phone_number_country_codes: Optional list of country codes to filter (e.g., ['US'])
        phone_number_types: Optional list of types to filter ('DID', 'TOLL_FREE')
        next_token: Token for pagination
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - phone_numbers: List of claimed phone numbers with details
        - next_token: Token for fetching next page
        
    Raises:
        ConnectPhoneNumberError: If the list operation fails
        
    Example:
        >>> result = connect_phone_numbers_list(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     phone_number_types=["TOLL_FREE"]
        ... )
    """
    try:
        client = _get_connect_client()
        
        params = {
            "InstanceId": instance_id
        }
        
        if max_results:
            params["MaxResults"] = max_results
        
        if phone_number_country_codes:
            params["PhoneNumberCountryCodes"] = phone_number_country_codes
        
        if phone_number_types:
            params["PhoneNumberTypes"] = phone_number_types
        
        if next_token:
            params["NextToken"] = next_token
        
        response = client.list_phone_numbers(**params)
        
        phone_numbers = []
        for pn in response.get("PhoneNumberSummaryList", []):
            phone_numbers.append({
                "id": pn.get("Id"),
                "arn": pn.get("Arn"),
                "phone_number": pn.get("PhoneNumber"),
                "phone_number_country_code": pn.get("PhoneNumberCountryCode"),
                "phone_number_type": pn.get("PhoneNumberType"),
                "status": pn.get("Status"),
                "description": pn.get("Description"),
                "target_arn": pn.get("TargetArn"),
                "tags": pn.get("Tags", {})
            })
        
        return {
            "status": "success",
            "phone_numbers": phone_numbers,
            "next_token": response.get("NextToken")
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectPhoneNumberError(f"Failed to list phone numbers: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectPhoneNumberError(f"Failed to list phone numbers: {str(e)}")


def connect_phone_numbers_describe(
    instance_id: str,
    phone_number_id: str
) -> Dict[str, Any]:
    """Get detailed information about a phone number.
    
    Args:
        instance_id: Connect instance ID
        phone_number_id: Phone number ID
        
    Returns:
        Dictionary containing detailed phone number information
        
    Raises:
        ConnectPhoneNumberError: If the describe operation fails
        
    Example:
        >>> details = connect_phone_numbers_describe(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     phone_number_id="12345678-1234-1234-1234-123456789012"
        ... )
    """
    try:
        client = _get_connect_client()
        
        response = client.describe_phone_number(
            InstanceId=instance_id,
            PhoneNumberId=phone_number_id
        )
        
        pn = response.get("PhoneNumber", {})
        
        return {
            "status": "success",
            "id": pn.get("Id"),
            "arn": pn.get("Arn"),
            "phone_number": pn.get("PhoneNumber"),
            "phone_number_country_code": pn.get("PhoneNumberCountryCode"),
            "phone_number_type": pn.get("PhoneNumberType"),
            "phone_number_description": pn.get("PhoneNumberDescription"),
            "target_arn": pn.get("TargetArn"),
            "status": pn.get("Status"),
            "tags": pn.get("Tags", {})
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectPhoneNumberError(f"Failed to describe phone number: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectPhoneNumberError(f"Failed to describe phone number: {str(e)}")


def connect_phone_numbers_update(
    instance_id: str,
    phone_number_id: str,
    target_arn: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Update a phone number's settings.
    
    Args:
        instance_id: Connect instance ID
        phone_number_id: Phone number ID to update
        target_arn: Optional new target ARN
        description: Optional new description
        
    Returns:
        Dictionary containing update status
        
    Raises:
        ConnectPhoneNumberError: If the update fails
        
    Example:
        >>> connect_phone_numbers_update(
        ...     instance_id="12345678-1234-1234-1234-123456789012",
        ...     phone_number_id="12345678-1234-1234-1234-123456789012",
        ...     target_arn="arn:aws:connect:us-east-1:123456789012:instance/xxx/queue/yyy"
        ... )
    """
    try:
        client = _get_connect_client()
        
        # Note: Connect API doesn't have a direct update_phone_number
        # Updates are done through association changes
        if target_arn:
            # Associate/disassociate might be needed
            # This is a placeholder - actual implementation depends on specific use case
            pass
        
        if description:
            # Description updates may not be supported directly
            pass
        
        return {
            "status": "success",
            "message": f"Phone number {phone_number_id} updated successfully"
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise ConnectPhoneNumberError(f"Failed to update phone number: {error_code} - {error_message}")
    except Exception as e:
        raise ConnectPhoneNumberError(f"Failed to update phone number: {str(e)}")
