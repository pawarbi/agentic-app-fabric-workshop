# below is a function to simulate content safety errors from Azure OpenAI for testing purposes.
def simulate_safety_error(hate_filtered=False, hate_severity="safe",
                            jailbreak_filtered=False, jailbreak_detected=False,
                            self_harm_filtered=False, self_harm_severity="safe",
                            sexual_filtered=False, sexual_severity="safe",
                            violence_filtered=False, violence_severity="safe"):
    """
    Simulates an Azure OpenAI BadRequestError for content safety testing.
    Use this to test error handling without actually triggering content filters.
    """
    from openai import BadRequestError
    import httpx
    
    content_filter_result = {
        "hate": {
            "filtered": hate_filtered,
            "severity": hate_severity
        },
        "jailbreak": {
            "filtered": jailbreak_filtered,
            "detected": jailbreak_detected
        },
        "self_harm": {
            "filtered": self_harm_filtered,
            "severity": self_harm_severity
        },
        "sexual": {
            "filtered": sexual_filtered,
            "severity": sexual_severity
        },
        "violence": {
            "filtered": violence_filtered,
            "severity": violence_severity
        }
    }
    
    # Mock error body matching Azure OpenAI's actual response structure
    mock_error_body = {
        "error": {
            "message": "The response was filtered due to the prompt triggering Azure OpenAI's content management policy. Please modify your prompt and retry. To learn more about our content filtering policies please read our documentation: https://go.microsoft.com/fwlink/?linkid=2198766",
            "type": None,
            "param": "prompt",
            "code": "content_filter",
            "status": 400,
            "innererror": {
                "code": "ResponsibleAIPolicyViolation",
                "content_filter_result": content_filter_result
            }
        }
    }
    # Create a proper mock request and response
    mock_request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    mock_response = httpx.Response(
        status_code=400,
        request=mock_request,
        json=mock_error_body
    )
    error_message = f"Error code: 400 - {mock_error_body}"
    
    # Create a mock BadRequestError with the body attribute
    error = BadRequestError(
        message=error_message,
        response=mock_response,
        body=mock_error_body
    )
    
    return error