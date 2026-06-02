# **1\. OBJETIVO TÉCNICO**

El objetivo técnico del MVP es desarrollar una infraestructura conversacional inteligente capaz de integrarse con la operativa real de una empresa utility para automatizar procesos de atención al abonado mediante inteligencia artificial conversacional.

La plataforma deberá ser capaz de:

* atender llamadas automáticamente  
* interpretar lenguaje natural  
* consultar información operativa en tiempo real  
* interpretar incidencias  
* automatizar respuestas  
* ejecutar acciones sobre sistemas internos  
* generar tickets automáticamente  
* derivar casos complejos a operadores humanos cuando sea necesario

La arquitectura no se plantea como:

* un chatbot tradicional  
* un IVR clásico  
* ni un asistente aislado

El objetivo es construir:

## **una capa operativa conversacional conectada a sistemas reales de empresa**

---

# **2\. ARQUITECTURA GENERAL**

La infraestructura estará dividida en varias capas desacopladas y escalables.

---

# **2.1 CAPA CONVERSACIONAL (VOICE LAYER)**

## **Descripción**

Responsable de toda la interacción por voz con el usuario.

---

## **Funciones principales**

* recepción de llamadas  
* STT (Speech To Text)  
* TTS (Text To Speech)  
* gestión del contexto conversacional  
* detección de intención  
* extracción de entidades  
* generación de respuestas dinámicas  
* gestión del flujo conversacional

---

## **Objetivo**

La conversación debe mantenerse natural y flexible, evitando árboles rígidos típicos de IVR tradicionales.

---

# **2.2 ORQUESTADOR CONVERSACIÓN**

# **Descripción**

Capa central encargada de coordinar toda la lógica conversacional y operativa del sistema.

---

## **Responsabilidades**

* mantener estado de conversación  
* gestionar contexto temporal  
* controlar memoria conversacional  
* decidir herramientas disponibles  
* validar acciones  
* controlar flujo operativo  
* gestionar confidence scoring  
* activar human handoff cuando sea necesario

---

## **Función dentro del sistema**

El orquestador actúa como núcleo coordinador entre:

* IA  
* herramientas operativas  
* bases de datos  
* sistemas externos  
* operadores humanos

---

# **2.3 MOTOR IA** 

## **Descripción**

Encargado de interpretar el contexto conversacional y operativo para tomar decisiones automáticas.

---

## **Funciones principales**

* clasificación de intención  
* interpretación de incidencias  
* priorización automática  
* detección de emergencias  
* evaluación de confianza  
* interpretación de estados operativos  
* clasificación de tickets  
* generación de respuestas dinámicas

---

## **Objetivo**

El sistema debe ser capaz de interpretar múltiples escenarios operativos en tiempo real utilizando contexto conversacional y datos internos.

---

# 

# **2.4 CAPA MCP** 

## **Descripción**

La capa MCP (Model Context Protocol) será la encargada de conectar la inteligencia artificial con los sistemas reales de la empresa.

Esta capa funcionará como intermediario entre la IA y la infraestructura operativa interna, permitiendo que el sistema pueda consultar información y ejecutar acciones sobre herramientas reales de forma segura y estructurada.

---

## **Sistemas conectados mediante MCP**

* APIs internas  
* bases de datos  
* sistemas de incidencias  
* ERPs  
* CRMs  
* herramientas operativas  
* sistemas de tickets  
* pasarelas de comunicación

---

## **Funciones principales**

* consulta de abonados  
* verificación de suministro  
* consulta de incidencias  
* revisión de expedientes  
* apertura automática de tickets  
* consulta de pagos  
* envío de información  
* ejecución de acciones operativas  
* derivación automática de llamadas

---

## **Objetivo**

La IA no solo responde:  
  también interactúa con sistemas reales mediante herramientas expuestas a través de MCP servers.

Esto permite construir una infraestructura conversacional desacoplada y escalable donde la lógica IA y la lógica operativa puedan evolucionar independientemente.

---

# **2.5 CAPA DE DATOS**

## **Descripción**

Infraestructura relacional orientada a gestión operativa.

---

## **Entidades principales**

* abonados  
* contratos  
* direcciones  
* incidencias  
* expedientes  
* tickets  
* llamadas  
* acciones IA  
* trazabilidad operativa

---

## **Objetivo**

Permitir navegación relacional eficiente entre entidades para que la IA pueda interpretar contexto operativo igual que un operador humano.

---

# 

# 

# 

# **2.6 INTERFAZ OPERATIVA**

## **Descripción**

Dashboard orientado a monitorización y supervisión del sistema.

---

## **Funcionalidades principales**

* llamadas activas  
* transcripciones en tiempo real  
* incidencias detectadas  
* tickets generados  
* estados operativos  
* acciones ejecutadas por IA  
* métricas operativas  
* handoffs humanos  
* volumen de incidencias  
* trazabilidad de conversaciones

---

# **3\. PIPELINE OPERATIVO**

## **Flujo técnico simplificado**

Llamada entrante

↓

Speech To Text (STT)

↓

Conversation Orchestrator

↓

Motor IA / Decision Engine

↓

MCP / Action Layer

↓

APIs / Bases de Datos / Sistemas internos

↓

Generación respuesta dinámica

↓

Text To Speech (TTS)

↓

Respuesta usuario

---

## **Objetivo del pipeline**

Permitir que la IA pueda:

* interpretar conversaciones  
* consultar información  
* ejecutar acciones  
* responder dinámicamente en tiempo real

---

# **4\. MODELO DE DATOS**

---

# **4.1 TABLA: ENTIDADES**

## **Descripción**

Representa la información principal del abonado o titular del suministro.

## **Campos**

* nif → PK  
* telefono → INDEX  
* apellidos → NOT NULL  
* dir\_fiscal → NOT NULL

## **Relación**

* una entidad puede tener múltiples contratos asociados

---

# **4.2 TABLA: CONTRATOS**

## **Descripción**

Representa el núcleo operativo principal del sistema.

## **Campos**

* id\_abonado → PK  
* id\_dir\_suministro → FK \-\> DIRECCIONES\_SUMINISTRO.id\_direccion  
* nif\_titular → FK \-\> ENTIDADES.nif  
* estado\_suministro → ENUM(activo, suspendido, baja)  
* fecha\_alta → NOT NULL  
* fecha\_baja → NULL

## **Relaciones**

* un contrato pertenece a una única dirección  
* un contrato puede tener múltiples recibos  
* un contrato puede tener múltiples expedientes históricos  
* un contrato puede tener múltiples contadores históricos

---

# **4.3 TABLA: DIRECCIONES\_SUMINISTRO**

## **Descripción**

Representa las ubicaciones físicas asociadas al suministro.

## **Campos**

* id\_direccion → PK  
* calle → NOT NULL  
* numero → NULL  
* portal → NULL  
* planta → NULL  
* letra → NULL  
* cod\_postal → NOT NULL

---

# **4.4 TABLA: CONTADORES**

## **Descripción**

Información histórica de contadores.

## **Campos**

* id\_contador → PK  
* id\_contrato → FK \-\> CONTRATOS.id\_abonado  
* num\_serie → NOT NULL  
* fecha\_alta → NOT NULL  
* fecha\_baja → NULL

---

# **4.5 TABLA: HISTORICO\_RECIBOS**

## **Descripción**

Información de facturación y pagos.

## **Campos**

* id\_recibo → PK  
* id\_contrato → FK \-\> CONTRATOS.id\_abonado  
* importe\_recibo → NOT NULL  
* forma\_pago → ENUM(efectivo, transferencia\_bancaria, domiciliado)  
* status\_pago → ENUM(pendiente, pagado)

---

# 

# **4.6 TABLA: EXPEDIENTES\_CORTE**

## **Descripción**

Gestión de expedientes relacionados con suspensión de suministro.

## **Campos**

* id\_expediente → PK  
* id\_contrato → FK \-\> CONTRATOS.id\_abonado  
* numero\_recibo → FK \-\> HISTORICO\_RECIBOS.id\_recibo  
* fecha\_corte → NOT NULL  
* status\_corte → ENUM(pendiente, ejecutado)

## **Restricción**

* solo puede existir un expediente activo simultáneamente por contrato

---

# **4.7 TABLA: INCIDENCIAS**

## **Descripción**

Representa incidencias globales del sistema.

## **Ejemplos**

* averías  
* cortes programados  
* incidencias operativas

## **Campos**

* id\_incidencia → PK  
* tipo → ENUM(averia, corte\_programado, corte\_impago)  
* fecha\_inicio → NOT NULL  
* hora\_inicio → NOT NULL  
* fecha\_fin → NULL  
* hora\_fin → NULL  
* fecha\_fin\_prevista → NULL  
* hora\_fin\_prevista → NULL

## **Relación**

* una incidencia puede afectar múltiples direcciones

---

# **4.8 TABLA: INCIDENCIA\_DIRECCIONES**

## **Descripción**

Tabla intermedia para relación N:M entre incidencias y direcciones.

## **Campos**

* id\_incidencia → FK \-\> INCIDENCIAS.id\_incidencia  
* id\_direccion → FK \-\> DIRECCIONES\_SUMINISTRO.id\_direccion

---

# **4.9 TABLA: PARTES\_TRABAJO**

## **Descripción**

Representa tickets o partes generados automáticamente.

## **Campos**

* id\_ticket → PK  
* id\_direccion → FK \-\> DIRECCIONES\_SUMINISTRO.id\_direccion  dir unica  
* id\_incidencia → FK \-\> INCIDENCIAS.id\_incidencia  
* fecha → NOT NULL  
* estado → ENUM(abierto, en\_proceso, cerrado)

---

# 

# **4.10 TABLA: LLAMADAS server mcp a parte**

## **Descripción**

Registro operativo de llamadas atendidas por IA.

## **Campos**

* id\_llamada → PK  
* telefono → INDEX  
* fecha\_inicio → NOT NULL  
* fecha\_fin → NULL  
* transcripcion → NULL  
* resumen\_ia → NULL  
* motivo\_detectado → NULL  
* human\_handoff → BOOLEAN  
* estado\_llamada → ENUM(completada, escalada, abandonada)

---

# **5\. FLUJOS OPERATIVOS**

---

# **5.1 ESCENARIO — FUGA EN VÍA PÚBLICA**

### **1\. Recepción llamada**

La IA recibe automáticamente la llamada.

---

### **2\. Identificación ubicación**

La IA solicita:

* calle  
* número aproximado  
* referencia cercana  
* municipio

---

### **3\. Consulta automática**

La IA consulta:

* incidencias activas  
* averías registradas  
* partes trabajo  
* incidencias relacionadas

---

### **4\. Interpretación automática**

### **Si existe incidencia:**

* informa estado actual

### **Si no existe:**

* genera incidencia automáticamente  
* crea parte trabajo  
* clasifica prioridad  
* notifica operativa

---

# **5.2 ESCENARIO — “NO TENGO AGUA”**

### **1\. Recepción llamada**

La IA recibe automáticamente la llamada.

---

### **2\. Identificación abonado**

La IA identifica automáticamente al usuario o solicita:

* NIF  
* teléfono  
* dirección  
* nombre completo

---

### 

### **3\. Consulta operativa**

La IA consulta:

* estado contrato  
* incidencias activas  
* cortes programados  
* expedientes  
* pagos pendientes

---

### **4\. Interpretación automática**

La IA determina automáticamente:

* avería activa  
* corte programado  
* expediente de corte  
* incidencia individual

---

### **5\. Respuesta dinámica**

Dependiendo del caso:

* informa incidencias  
* genera tickets  
* envía información  
* deriva operadores  
* ejecuta acciones automáticas

---

# **6\. HUMAN HANDOFF**

## **Activación automática**

Cuando el sistema detecte:

* baja confianza  
* incidencias complejas  
* emergencias  
* conversación conflictiva

👉 la llamada será transferida automáticamente a un operador humano.

---

## **Información generada antes de transferir**

La IA generará automáticamente:

* resumen contextual  
* ubicación  
* incidencias detectadas  
* acciones ejecutadas  
* prioridad caso

---

# **7\. OBSERVABILIDAD Y TRAZABILIDAD**

## **Funcionalidades**

La infraestructura contará con mecanismos de monitorización y trazabilidad para:

* registro de llamadas  
* auditoría de acciones IA  
* seguimiento incidencias  
* métricas operativas

## **Objetivo**

Garantizar:

* trazabilidad  
* auditoría  
* control operativo  
* debugging  
* mejora continua sistema

---

# 

# **8\. MULTICANALIDAD**

## **Canales soportados por arquitectura**

Aunque el MVP inicial se centra en voz, la infraestructura está diseñada para operar sobre:

* voz  
* WhatsApp  
* correo electrónico  
* aplicaciones móviles

## **Objetivo**

Mantener una capa conversacional unificada independientemente del canal utilizado por el usuario.

---

# **9\. OBJETIVO DEL MVP**

## **Objetivos principales**

* validar capacidad conversacional  
* validar integración con sistemas reales  
* automatizar procesos operativos  
* generar incidencias automáticamente  
* reducir carga operativa  
* validar viabilidad infraestructura conversacional utilities

