# SuperDulces BI

Sistema de inteligencia de negocio, analítica comercial y automatización operativa para integración con SysCafé.

---

# Descripción

SuperDulces BI es una plataforma desarrollada para centralizar, analizar y visualizar información operativa proveniente del ERP SysCafé, permitiendo transformar datos transaccionales en métricas de negocio útiles para la toma de decisiones.

El proyecto nace a partir de la necesidad de reducir procesos manuales y mejorar la visibilidad comercial y administrativa de una PYME del sector retail/dulcería.

Actualmente el sistema contempla:

* dashboards de ventas,
* métricas comerciales,
* análisis de inventario,
* productos más y menos vendidos,
* análisis financiero básico,
* integración con respaldos SysCafé,
* y automatización parcial del ingreso de facturas.

---

# Objetivos del Proyecto

## Inteligencia de negocio

Permitir a la organización visualizar información clave como:

* ventas por fecha,
* productos más vendidos,
* ticket promedio,
* ingresos,
* IVA generado,
* comportamiento comercial,
* rotación de inventario,
* tendencias de ventas.

---

## Automatización operativa

Reducir procesos manuales mediante:

* importación automatizada de compras,
* homologación de referencias de proveedores,
* procesamiento estructurado de archivos SysCafé,
* preparación de archivos compatibles para importación.

---

# Arquitectura General

```text
SysCafé DBF Backups
        ↓
Python ETL
        ↓
PostgreSQL
        ↓
FastAPI Backend
        ↓
React Dashboard
```

---

# Stack Tecnológico

## Frontend

* React
* TypeScript
* Vite
* TailwindCSS
* shadcn/ui
* Recharts

---

## Backend

* Python
* FastAPI
* SQLAlchemy
* Alembic
* PostgreSQL

---

## ETL / Data Processing

* Pandas
* dbfread
* Python ETL pipelines

---

## Infraestructura

* Docker
* Docker Compose
* Railway / Render (MVP deployment)

---

# Estructura del Proyecto

```text
superdulces-bi/
│
├── apps/
│   ├── frontend/
│   └── backend/
│
├── services/
│   └── etl/
│
├── database/
│   ├── migrations/
│   ├── schema/
│   ├── seeds/
│   └── init/
│
├── storage/
│   ├── raw/
│   ├── processed/
│   └── exports/
│
├── docs/
│
├── docker-compose.yml
│
└── README.md
```

---

# Flujo de Datos

## 1. Extracción

El sistema procesa respaldos y archivos DBF provenientes de SysCafé.

---

## 2. Transformación

Los datos son normalizados y limpiados mediante pipelines ETL desarrollados en Python.

---

## 3. Persistencia

La información procesada es almacenada en PostgreSQL para consultas analíticas eficientes.

---

## 4. Visualización

Los dashboards permiten visualizar métricas comerciales y operativas en tiempo real o por periodos históricos.

---

# Funcionalidades Planeadas

## Dashboard Comercial

* ventas diarias
* ventas mensuales
* top productos
* productos baja rotación
* ticket promedio
* ventas por caja
* comportamiento histórico

---

## Dashboard Inventario

* stock por bodega
* rotación inventario
* productos sin movimiento
* alertas de inventario

---

## Dashboard Financiero

* ingresos
* IVA generado
* comparativos mensuales
* tendencias

---

## Automatización Facturas

* procesamiento de compras externas
* homologación de referencias
* generación automática de archivos compatibles SysCafé

---

# Estado Actual

## Investigación técnica completada

Se validó exitosamente:

* acceso estructurado a respaldos SysCafé,
* lectura de archivos DBF,
* extracción de información transaccional,
* identificación de movimientos de ventas,
* y viabilidad técnica de integración BI.

---

# Seguridad

El proyecto trabaja inicialmente sobre copias de respaldo y archivos exportados, evitando afectar la operación productiva del ERP principal.

No se almacenan credenciales ni información sensible dentro del repositorio.

---

# Roadmap

## Fase 1

* extracción DBF
* ETL inicial
* consolidación PostgreSQL

## Fase 2

* APIs métricas
* dashboard MVP

## Fase 3

* automatización compras
* homologación referencias

## Fase 4

* sincronización automatizada
* analítica avanzada
* predicciones y recomendaciones

---

# Notas Importantes

* Los archivos DBF y respaldos productivos no deben subirse al repositorio.
* El proyecto utiliza `.gitignore` para evitar exposición de información sensible.
* Toda integración inicial se realiza en modo lectura/no invasivo.

---

# Autor

Proyecto desarrollado por: Juan Miguel Florez Vasquez

Ingeniería de Sistemas y Computación
Colombia
