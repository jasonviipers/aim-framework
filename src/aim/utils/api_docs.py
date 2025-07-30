"""
API Documentation Generator for the AIM Framework.

This module automatically generates OpenAPI/Swagger documentation
for the AIM Framework API endpoints.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class APIDocGenerator:
    """Generates OpenAPI 3.0 documentation for the AIM Framework API."""
    
    def __init__(self, version: str = "1.0.0", title: str = "AIM Framework API"):
        self.version = version
        self.title = title
        self.base_doc = self._create_base_doc()
    
    def _create_base_doc(self) -> Dict[str, Any]:
        """Create the base OpenAPI document structure."""
        return {
            "openapi": "3.0.3",
            "info": {
                "title": self.title,
                "description": "Advanced Intelligence Management Framework API",
                "version": self.version,
                "contact": {
                    "name": "AIM Framework Support",
                    "email": "support@aimframework.com"
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT"
                }
            },
            "servers": [
                {
                    "url": "http://localhost:5000",
                    "description": "Development server"
                },
                {
                    "url": "https://api.aimframework.com",
                    "description": "Production server"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "responses": {},
                "parameters": {},
                "securitySchemes": {
                    "ApiKeyAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key"
                    },
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            },
            "security": [],
            "tags": [
                {
                    "name": "health",
                    "description": "Health check and system status"
                },
                {
                    "name": "agents",
                    "description": "Agent management operations"
                },
                {
                    "name": "processing",
                    "description": "Request processing operations"
                },
                {
                    "name": "context",
                    "description": "Context management operations"
                },
                {
                    "name": "metrics",
                    "description": "Performance metrics and monitoring"
                }
            ]
        }
    
    def generate_documentation(self) -> Dict[str, Any]:
        """Generate complete API documentation."""
        doc = self.base_doc.copy()
        
        # Add all endpoint definitions
        doc["paths"].update(self._get_health_endpoints())
        doc["paths"].update(self._get_agent_endpoints())
        doc["paths"].update(self._get_processing_endpoints())
        doc["paths"].update(self._get_context_endpoints())
        doc["paths"].update(self._get_metrics_endpoints())
        
        # Add schema definitions
        doc["components"]["schemas"].update(self._get_schemas())
        doc["components"]["responses"].update(self._get_common_responses())
        
        return doc
    
    def _get_health_endpoints(self) -> Dict[str, Any]:
        """Define health check endpoints."""
        return {
            "/health": {
                "get": {
                    "tags": ["health"],
                    "summary": "Health check",
                    "description": "Check the health status of the API server",
                    "operationId": "getHealth",
                    "responses": {
                        "200": {
                            "description": "Health status",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/HealthResponse"}
                                }
                            }
                        },
                        "503": {
                            "description": "Service unavailable",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _get_agent_endpoints(self) -> Dict[str, Any]:
        """Define agent management endpoints."""
        return {
            "/agents": {
                "get": {
                    "tags": ["agents"],
                    "summary": "List agents",
                    "description": "Get a list of all available agents",
                    "operationId": "listAgents",
                    "responses": {
                        "200": {
                            "description": "List of agents",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AgentListResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/agents/{agent_id}": {
                "get": {
                    "tags": ["agents"],
                    "summary": "Get agent details",
                    "description": "Get detailed information about a specific agent",
                    "operationId": "getAgent",
                    "parameters": [
                        {
                            "name": "agent_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Agent identifier"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Agent details",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AgentResponse"}
                                }
                            }
                        },
                        "404": {
                            "description": "Agent not found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _get_processing_endpoints(self) -> Dict[str, Any]:
        """Define request processing endpoints."""
        return {
            "/process": {
                "post": {
                    "tags": ["processing"],
                    "summary": "Process request",
                    "description": "Process a request using the AIM Framework",
                    "operationId": "processRequest",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ProcessRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Processing result",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ProcessResponse"}
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "429": {
                            "description": "Rate limit exceeded",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _get_context_endpoints(self) -> Dict[str, Any]:
        """Define context management endpoints."""
        return {
            "/context": {
                "post": {
                    "tags": ["context"],
                    "summary": "Create context",
                    "description": "Create a new context thread",
                    "operationId": "createContext",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/CreateContextRequest"}
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Context created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ContextResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/context/{context_id}": {
                "get": {
                    "tags": ["context"],
                    "summary": "Get context",
                    "description": "Get context thread details",
                    "operationId": "getContext",
                    "parameters": [
                        {
                            "name": "context_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Context identifier"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Context details",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ContextResponse"}
                                }
                            }
                        },
                        "404": {
                            "description": "Context not found",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _get_metrics_endpoints(self) -> Dict[str, Any]:
        """Define metrics and monitoring endpoints."""
        return {
            "/metrics": {
                "get": {
                    "tags": ["metrics"],
                    "summary": "Get metrics",
                    "description": "Get performance metrics and system status",
                    "operationId": "getMetrics",
                    "parameters": [
                        {
                            "name": "hours",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 1},
                            "description": "Number of hours of metrics to retrieve"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Performance metrics",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/MetricsResponse"}
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _get_schemas(self) -> Dict[str, Any]:
        """Define data schemas."""
        return {
            "HealthResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["healthy", "unhealthy"]},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "uptime": {"type": "number"},
                    "version": {"type": "string"},
                    "details": {"type": "object"}
                },
                "required": ["status", "timestamp", "uptime", "version"]
            },
            "ProcessRequest": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Request message"},
                    "agent_id": {"type": "string", "description": "Target agent ID"},
                    "context_id": {"type": "string", "description": "Context thread ID"},
                    "priority": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5},
                    "metadata": {"type": "object", "description": "Additional metadata"}
                },
                "required": ["message"]
            },
            "ProcessResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "result": {"type": "object"},
                    "message": {"type": "string"},
                    "processing_time": {"type": "number"},
                    "agent_id": {"type": "string"},
                    "context_id": {"type": "string"}
                },
                "required": ["success", "result"]
            },
            "AgentListResponse": {
                "type": "object",
                "properties": {
                    "agents": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Agent"}
                    },
                    "total": {"type": "integer"}
                },
                "required": ["agents", "total"]
            },
            "Agent": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "status": {"type": "string", "enum": ["active", "inactive", "error"]},
                    "capabilities": {"type": "array", "items": {"type": "string"}},
                    "metadata": {"type": "object"}
                },
                "required": ["id", "name", "type", "status"]
            },
            "AgentResponse": {
                "type": "object",
                "properties": {
                    "agent": {"$ref": "#/components/schemas/Agent"}
                },
                "required": ["agent"]
            },
            "CreateContextRequest": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "metadata": {"type": "object"}
                },
                "required": ["user_id"]
            },
            "ContextResponse": {
                "type": "object",
                "properties": {
                    "context_id": {"type": "string"},
                    "user_id": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "metadata": {"type": "object"}
                },
                "required": ["context_id", "user_id", "created_at"]
            },
            "MetricsResponse": {
                "type": "object",
                "properties": {
                    "current": {"$ref": "#/components/schemas/PerformanceMetrics"},
                    "history": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/PerformanceMetrics"}
                    }
                },
                "required": ["current"]
            },
            "PerformanceMetrics": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string", "format": "date-time"},
                    "cpu_usage": {"type": "number"},
                    "memory_usage": {"type": "number"},
                    "disk_usage": {"type": "number"},
                    "request_count": {"type": "integer"},
                    "response_time_avg": {"type": "number"},
                    "error_rate": {"type": "number"},
                    "active_connections": {"type": "integer"}
                },
                "required": ["timestamp", "cpu_usage", "memory_usage"]
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                    "message": {"type": "string"},
                    "code": {"type": "integer"},
                    "timestamp": {"type": "string", "format": "date-time"}
                },
                "required": ["error", "message"]
            }
        }
    
    def _get_common_responses(self) -> Dict[str, Any]:
        """Define common response templates."""
        return {
            "BadRequest": {
                "description": "Bad request",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                    }
                }
            },
            "NotFound": {
                "description": "Resource not found",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                    }
                }
            },
            "InternalServerError": {
                "description": "Internal server error",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                    }
                }
            },
            "RateLimitExceeded": {
                "description": "Rate limit exceeded",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                    }
                }
            }
        }
    
    def save_to_file(self, filename: str = "api_docs.json"):
        """Save the generated documentation to a file."""
        doc = self.generate_documentation()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
    
    def get_swagger_ui_html(self, api_url: str = "/api/docs.json") -> str:
        """Generate HTML for Swagger UI."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>AIM Framework API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *, *:before, *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin:0;
            background: #fafafa;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                url: '{api_url}',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            }});
        }};
    </script>
</body>
</html>
        """.strip()


def generate_api_docs(output_file: str = "docs/api_documentation.json"):
    """Generate and save API documentation."""
    generator = APIDocGenerator()
    generator.save_to_file(output_file)
    return generator.generate_documentation()


if __name__ == "__main__":
    # Generate documentation
    docs = generate_api_docs()
    print("API documentation generated successfully!")
    print(f"Total endpoints: {len(docs['paths'])}")
    print(f"Total schemas: {len(docs['components']['schemas'])}")