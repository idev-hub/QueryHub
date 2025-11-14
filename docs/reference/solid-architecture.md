# QueryHub Architecture - SOLID Principles

## Overview
QueryHub follows SOLID principles and clean architecture patterns to ensure maintainability, testability, and extensibility.

## SOLID Principles Implementation

### Single Responsibility Principle (SRP)

Each class has one reason to change:

1. **ComponentExecutor** - Only executes individual components
2. **ProviderResolver** - Only manages provider lifecycle
3. **ReportExecutor** - Only orchestrates report execution
4. **MessageBuilder** - Only builds email messages
5. **RecipientResolver** - Only resolves email recipients
6. **SubjectFormatter** - Only formats email subjects
7. **DataExtractor** - Only extracts and normalizes data
8. **YAMLFileReader** - Only reads YAML files
9. **EnvironmentSubstitutor** - Only handles environment variable substitution
10. **ConfigParser** - Only parses and validates configuration

### Open/Closed Principle (OCP)

The system is open for extension but closed for modification:

1. **Provider Registry** - New providers can be added without modifying existing code
2. **Renderer Registry** - New renderers can be registered without changing core
3. **Retry Strategy** - New retry strategies can be implemented via interface
4. **Credential Types** - New credential types can be added via discriminated unions

### Liskov Substitution Principle (LSP)

Subtypes are substitutable for their base types:

1. **QueryProvider** - All provider implementations can be used interchangeably
2. **ComponentRenderer** - All renderers follow the same contract
3. **RetryStrategy** - Different retry strategies are substitutable
4. **AsyncResource** - All resources follow the same lifecycle

### Interface Segregation Principle (ISP)

Clients depend only on interfaces they use:

1. **ProviderFactoryProtocol** - Only `create()` method
2. **RendererResolverProtocol** - Only `resolve()` method
3. **ReportTemplateEngine** - Only `render()` method
4. **EmailSenderProtocol** - Only `send_report()` method
5. **ConfigLoaderProtocol** - Only `load()` method

### Dependency Inversion Principle (DIP)

High-level modules depend on abstractions, not concretions:

1. **ReportExecutor** depends on:
   - `ProviderFactoryProtocol` (not concrete factory)
   - `RendererResolverProtocol` (not concrete registry)
   - `ReportTemplateEngine` (not Jinja directly)

2. **ComponentExecutor** depends on:
   - `ProviderResolver` (abstraction over provider management)
   - `RendererResolverProtocol` (not concrete renderers)

3. **QueryHubApplicationBuilder** (Composition Root):
   - Wires all dependencies together
   - Allows dependency injection for testing
   - Provides sensible defaults

## Design Patterns

### Creational Patterns

1. **Factory Pattern** - `ProviderFactory`, `ProviderRegistry`
2. **Builder Pattern** - `QueryHubApplicationBuilder`
3. **Registry Pattern** - `ProviderRegistry`, `RendererRegistry`

### Structural Patterns

1. **Facade Pattern** - `EmailClient`, `ConfigLoader`
2. **Adapter Pattern** - Provider implementations adapt different data sources
3. **Decorator Pattern** - `RetryStrategy` wraps operations

### Behavioral Patterns

1. **Strategy Pattern** - `ComponentRenderer`, `RetryStrategy`
2. **Template Method** - `QueryProvider` with hook methods
3. **Observer Pattern** - Async event handling in executors

## Error Hierarchy

Centralized error hierarchy in `core/errors.py`:

- `QueryHubError` (base)
  - `ConfigurationError`
  - `ProviderError`
    - `ProviderExecutionError`
    - `ProviderNotFoundError`
    - `ProviderInitializationError`
  - `RenderingError`
  - `TemplateError`
  - `EmailError`
  - `ExecutionTimeoutError`
  - `ResourceError`

## Resource Management

1. **ResourcePool** - Thread-safe lazy initialization with proper cleanup
2. **ResourceManager** - Coordinates multiple resource lifecycles
3. **ProviderResolver** - Manages provider instances with proper shutdown

## Testing Strategy

The architecture supports:

1. **Unit Testing** - Each component is independently testable
2. **Integration Testing** - Protocols allow easy mocking
3. **Contract Testing** - Interfaces define clear contracts
4. **Dependency Injection** - All dependencies can be replaced for testing

## Module Organization

```
queryhub/
├── core/           # Core abstractions and contracts
│   ├── contracts.py       # Protocol definitions (ISP)
│   ├── errors.py          # Error hierarchy
│   ├── providers.py       # Provider registry and factory
│   ├── retry.py           # Retry strategies
│   └── resource_manager.py # Resource lifecycle management
├── config/         # Configuration management (SRP)
│   ├── environment.py     # Environment substitution
│   ├── loader.py          # Configuration loading
│   └── models.py          # Configuration models
├── providers/      # Data source implementations (OCP)
│   ├── base.py            # Provider abstraction
│   ├── adx.py             # Azure Data Explorer
│   ├── sql.py             # SQL databases
│   ├── rest.py            # REST APIs
│   └── csv.py             # CSV files
├── rendering/      # HTML rendering (OCP, Strategy)
│   ├── renderers.py       # Renderer implementations
│   ├── jinja_env.py       # Jinja configuration
│   └── template_engine.py # Template engine
├── services/       # Business logic (SRP, DIP)
│   ├── application.py     # Application builder
│   ├── component_executor.py # Component execution
│   └── executor.py        # Report execution
├── email/          # Email delivery (SRP, Facade)
│   └── client.py          # SMTP client
└── cli.py          # Command-line interface

```

## Benefits of This Architecture

1. **Maintainability** - Clear separation of concerns makes code easier to understand
2. **Testability** - Dependency injection and protocols enable comprehensive testing
3. **Extensibility** - New providers, renderers, and strategies can be added easily
4. **Reliability** - Proper error handling and resource management
5. **Type Safety** - Strong typing with protocols and generics
6. **Documentation** - Self-documenting through clear interfaces and contracts

## Best Practices Applied

1. ✅ Immutable data classes where appropriate
2. ✅ Type hints on all public interfaces
3. ✅ Docstrings on all public methods
4. ✅ Proper async/await patterns
5. ✅ Thread-safe lazy initialization
6. ✅ Comprehensive error handling
7. ✅ Resource cleanup with context managers
8. ✅ Logging at appropriate levels
9. ✅ Configuration validation
10. ✅ Separation of I/O and business logic
