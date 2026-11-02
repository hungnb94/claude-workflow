# Platforms

Registry read at Step 1 of `SKILL.md`. Each `##` section is one platform. To add a platform, add a section here; do not edit `SKILL.md`.

Every section has a **Detect** line. A section is either:

- Self-described: **Standard architecture**, **Patterns**, **Anti-patterns**, **Outdated signals**.
- Pointer: **Standards** only. The standards file is the single source of truth, so do not copy its content here.

Platforms: Android, Kotlin Multiplatform, iOS, Flutter, Web frontend, Backend.

## Android

- **Detect**: a Gradle build file that applies an Android application or library plugin; an Android manifest; `src/main` with `res/`.
- **Standards**: Read `standards.md` in the `android-standards-workflow` skill folder. Look it up in this order: (1) `../android-standards-workflow/standards.md` next to this skill's "Base directory"; (2) Glob `**/android-standards-workflow/standards.md`; (3) if still missing, tell the user and continue with general best practice. Do not copy its content here. It also holds the migration rules for outdated tech.

## Kotlin Multiplatform

- **Detect**: the Kotlin multiplatform Gradle plugin in a build file; `commonMain/` and per-target source set folders. A project that also has the Android plugin is still Kotlin Multiplatform.
- **Standards**: Read `standards.md` in the `kmp-standards-workflow` skill folder, with the same lookup order as Android (replace the skill name). Do not copy its content here. It also holds the migration rules for outdated tech.

## iOS

- **Detect**: an Xcode project or workspace; a Swift package manifest; `.swift` sources with an app target and `Info.plist`.
- **Standard architecture**: UI (Views) / presentation (ViewModels) / domain (use cases, optional) / data (repositories, services).
- **Patterns**: MVVM with SwiftUI and observable state; unidirectional data flow; repository over network and persistence; dependency injection by initializer or environment; structured concurrency (async/await, actors); coordinator or typed navigation path for flow.
- **Anti-patterns**: massive view controller; business logic inside views; singletons as hidden dependencies; shared mutable state without actor isolation; force unwraps on external data; completion-handler pyramids in new code.
- **Outdated signals**: Objective-C sources; UIKit-only screens with storyboards in a project that targets modern SwiftUI; completion handlers or Combine chains where async/await is available; `ObservableObject` where the Observation framework is available.

## Flutter

- **Detect**: `pubspec.yaml` with a `flutter:` key; `lib/main.dart`. A Flutter project often has an `android/` or `ios/` folder; it is still Flutter.
- **Standard architecture**: UI layer (views and view models) / data layer (repositories and services). A domain layer is optional for complex logic.
- **Patterns**: MVVM; repository as single source of truth; immutable state; unidirectional data flow; dependency injection with a provider-style package; feature-first folders; a typed router.
- **Anti-patterns**: business logic in widgets; `setState` for state shared across screens; widgets calling network or storage directly; god view models; deep widget trees without extraction; unbounded `BuildContext` passing into logic.
- **Outdated signals**: no null safety; `scoped_model` or very old state packages; deprecated navigator-1 route tables in a project that uses a router package; widgets from deprecated APIs flagged by the analyzer.

## Web frontend

- **Detect**: a package manifest with a UI framework dependency; a bundler or framework config; `src/` with components, pages or routes.
- **Standard architecture**: components (presentational) / feature modules (containers, hooks or services) / data access (API client, query cache) / shared UI and utilities.
- **Patterns**: component composition; colocated feature folders; server state in a query cache, client state kept small; typed API client; accessibility by default; code splitting by route; error and loading boundaries; tests at the component and user-flow level.
- **Anti-patterns**: prop drilling through many levels; global store for server data; business logic in presentational components; fetching inside deeply nested components; untyped API responses; barrel files that break tree shaking.
- **Outdated signals**: AngularJS (1.x); class components and legacy lifecycle methods in a hooks-based codebase; Create React App tooling; jQuery-driven DOM updates; JavaScript without types in a project that already uses TypeScript elsewhere.

## Backend

- **Detect**: a server framework dependency; controllers, routes or handlers; database migrations; a Dockerfile or deployment descriptor; no UI sources.
- **Standard architecture**: transport (controllers, handlers) / application (use cases) / domain (entities, rules) / infrastructure (persistence, messaging, external clients).
- **Patterns**: layered or hexagonal architecture; repository over persistence; DTOs at the boundary; input validation at the edge; idempotent writes and retries for external calls; transactions around one use case; structured logging, metrics and tracing; configuration from the environment; versioned APIs; migrations in version control.
- **Anti-patterns**: business logic in controllers; domain entities leaked as API responses; N+1 queries; shared mutable state across requests; swallowed exceptions; secrets in code; chatty calls between services without timeouts.
- **Outdated signals**: raw SQL string concatenation; unsupported runtime or framework versions; synchronous blocking calls in an async stack; hand-rolled auth or password hashing; schema changes applied by hand.
