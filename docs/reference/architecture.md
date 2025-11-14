# QueryHub SOLID Architecture

## Current Limitations

- **Single Responsibility:** Core services such as `ReportExecutor` construct providers, renderers, template engines, and SMTP clients internally, forcing unrelated responsibilities into one class.
- **Open/Closed:** Adding a provider or renderer requires editing `ReportExecutor` or singleton registries because extension points are hard-coded rather than registered behind abstractions.
- **Liskov & Interface Segregation:** Concrete classes are passed around instead of narrow interfaces, making it difficult to stub dependencies in tests or to substitute alternate implementations.
- **Dependency Inversion:** High-level flows (`cli`, `services.executor`) depend directly on low-level modules (Kusto client, SQLAlchemy, Jinja) instead of interfaces, preventing composition roots or dependency injection.
- **Global State & Singleton Patterns:** Module-level registries (renderers, provider classes, cached template environments) hide stateful logic, complicating concurrency and violating user requirements for a singleton-free design.

## Target SOLID Design

1. **Contracts Module (`queryhub.core.contracts`)**
   - `ConfigLoaderProtocol`: asynchronous loader abstraction returning `Settings`.
   - `ProviderFactoryProtocol`: resolves `QueryProvider` instances by ID.
   - `RendererResolverProtocol`: maps `ComponentRenderConfig` to `ComponentRenderer` implementations.
   - `ReportTemplateEngine`: produces HTML from a `ReportConfig`, template name, and context.
   - `EmailSenderProtocol`: sends a `ReportExecutionResult` using injected transports.

2. **Composed Factories (No Singletons)**
   - `ProviderRegistry` + `DefaultProviderFactory` assemble providers from a mapping of `ProviderType → constructor` supplied at runtime.
   - `RendererRegistry` instances own their registrations; callers dispose/replace them without touching globals.
   - `JinjaReportTemplateEngine` receives a `jinja2.Environment` created per application instance, ensuring template concerns remain isolated.

3. **Application Builder**
   - `QueryHubApplicationBuilder` (in `queryhub.services.application`) acts as a composition root: it wires a config loader, provider factory, renderer registry, template engine, and email sender into a ready-to-use `ReportExecutor`.
   - Builders accept overrides for every dependency, enabling tests or hosts to plug custom implementations while the CLI simply builds the defaults.

4. **Executor Refactor**
   - `ReportExecutor` now depends only on injected interfaces. It coordinates report execution, rendering, and metadata aggregation while delegating provider creation and HTML rendering to collaborators.
   - Provider caching and retry logic remain encapsulated within the executor but rely on abstract factories instead of instantiating concretes.

5. **Extensibility & Testing**
   - New providers or renderers register through builder hooks rather than editing core modules.
   - Tests can pass in fake factories, renderers, or template engines, reducing the need for patching network clients.

This design keeps each component focused on a single responsibility, encourages extension via registration rather than modification, segregates interfaces so consumers depend only on what they use, and inverts infrastructure dependencies toward the application boundary.
