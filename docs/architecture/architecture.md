# Algorithm Management Toolkit Architecture

This document contains architectural decisions related to the Algorithm Managment Toolkit.

## System Context
The Algorithm Management Toolkit is an application that users can use to complete requirements
that are specified by the algoritmekader. The diagram below sketches the broader system context
of this Algorithm Management Toolkit.

### Example
Suppose a data science team is working on an ML-algorithm. A team member visits the Algoritmekader
website and sees that among other things an IAMA is a required to be performed. The user selects
the IAMA task from the Algoritmekader and is forwarded to the Algorithm Management Toolkit. Here
the user can login and import the IAMA task. The Algorithm Management Toolkit imports the instructions
on how to execute an IAMA and how to store the results from the Instrument Register. Now the user can
perform the IAMA from within the Algorithm Management Toolkit. Relevant stakeholders can also login
to the project page of the Algorithm Management Toolkit to answer questions from the IAMA. Relevant
discussions can be captured within the toolkit as well. Upon completion the IAMA results are written
to an Assessment Card within a System Card to a user specified location, usually a remote repository
where the source code of the algorithm resides.

```mermaid
C4Context
    title System Context diagram for Algorithm Management Toolkit
    Boundary(b0, "Government of the Netherlands") {
        System(Algoritmekader, "Algoritmekader", "Defines measures and instruments")
        System(TAD, "Algorithm Management Toolkit", "Provides the execution of measures and instruments")
        System(InstrumentRegister, "Instrument Register", "Contains information about how to execute instruments and measures")
        System(Repository, "Repository", "Contains a System Card with filled in measures and instruments")
    }

    Person(user0, "User", "User wants to comply with regulations and required
    ethical frameworks")


    Rel(Algoritmekader, TAD, "Passes required measures and instruments")
    UpdateRelStyle(Algoritmekader, TAD, $offsetY="50", $offsetX="-150")
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")

    Rel(TAD, Repository, "Writes results to a System Card")
    UpdateRelStyle(TAD, Repository, $offsetY="15", $offsetX="0")
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")

    Rel(InstrumentRegister, TAD, "Specifies instructions on how to execute instruments and measures")
    UpdateRelStyle(InstrumentRegister, TAD, $offsetY="50", $offsetX="-40")
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")


    Rel(user0, Algoritmekader, "Selects which measures and instruments need to be exectued")
    UpdateRelStyle(user0, Algoritmekader, $offsetY="-30", $offsetX="-320")

    Rel(user0, TAD, "Executes the required measures and instruments")
    UpdateRelStyle(user0, TAD, $offsetY="-30", $offsetX="-30")
```

## Container Diagram of the Algorithm Management Toolkit System
```mermaid
C4Container
    title Container diagram for the Algorithm Management Toolkit System
    Person(user0, "User", "A user of the the Algorithm Management Toolkit")
    System(Repository, "Repository", "External repository where the System Card will be stored")
    System(InstrumentRegister, "Instrument Register", "Contains information about how to execute instruments and measures")

    Boundary(b0, "Algorithm Management Toolkit") {

        Container(FrontEnd, "Front End", "htmx, jinja2", "Provides user interface for projects <br/> and tasks")
        Container(API, "API Application", "Python, FastAPI", "Provides the project and task management <br/> functionality via HTTPS.")
        Container(Business Logic, "Business Logic", "Python", "Core logic of the <br/> Algorithm Management Toolkit")
        Container(State, "System State", "", "Provides the state of the <br/>Algorithm Management Toolkit")
        Container(CLI, "CLI", "TODO", "CLI to execute measures <br/> and instruments")
        Container(Tasks, "Tasks", "Python library", "Library containing executable tasks <br/> which are measures and instruments")
        Container(Queue, "Task Queue", "Celery, Redis", "Asynchronously manages and <br/>executes tasks")
        SystemDb(Db, "Database")
    }


    Rel(user0, CLI, "Executes tasks locally from", "Command line")
    UpdateRelStyle(user0, CLI, $offsetY="-170", $offsetX="-170")

    Rel(user0, FrontEnd, "Visits Algorithm Management Toolkit webpage", "HTTPS")
    UpdateRelStyle(user0, FrontEnd, $offsetY="-60", $offsetX="10")

    Rel(Queue, Tasks, "Get tasks")
    UpdateRelStyle(Queue, Tasks, $offsetY="10", $offsetX="-30")

    Rel(CLI, Tasks, "Imports tasks from")
    UpdateRelStyle(CLI, Tasks, $offsetY="-20", $offsetX="-48")

    Rel(Tasks, API, "Sends live update","websocket")
    UpdateRelStyle(Tasks, API, $offsetY="-20", $offsetX="-100")

    Rel(API, FrontEnd, "Sends live update","websocket")
    UpdateRelStyle(API, FrontEnd, $offsetY="-40", $offsetX="-50")

    Rel(FrontEnd, API, "Makes API calls to", "HTTPS")
    UpdateRelStyle(FrontEnd, API, $offsetY="30", $offsetX="-50")

    Rel(State, Db, "Reads form and <br/>writes to", "")
    UpdateRelStyle(State, Db, $offsetY="-15", $offsetX="20")

    Rel(Business Logic, Db, "Reads form and <br/>writes to", "")
    UpdateRelStyle(Business Logic, Db, $offsetY="-20", $offsetX="-20")

    Rel(Business Logic, InstrumentRegister, "Gets instructions on how to execute tasks and <br/> store results", "")
    UpdateRelStyle(Business Logic, InstrumentRegister, $offsetY="-50", $offsetX="20")

    Rel(Business Logic, Queue, "Ask for task execution", "")
    UpdateRelStyle(Business Logic, Queue, $offsetY="-15", $offsetX="-130")

    Rel(Queue, Business Logic, "Gives task result", "")
    UpdateRelStyle(Queue, Business Logic, $offsetY="-15", $offsetX="10")

    Rel(Business Logic, Repository, "Writes System Card", "")
    UpdateRelStyle(Business Logic, Repository, $offsetY="-50", $offsetX="-130")

    Rel(API, Business Logic, "Forwards instructions", "")
    UpdateRelStyle(API, Business Logic, $offsetY="40", $offsetX="-50")

    Rel(Business Logic, API, "Returns results", "")
    UpdateRelStyle(Business Logic, API, $offsetY="20", $offsetX="-40")

    Rel(Business Logic, State, "Updates state", "")
    UpdateRelStyle(Business Logic, State, $offsetY="30", $offsetX="-30")

    Rel(State, Business Logic, "Gets state", "")
    UpdateRelStyle(State, Business Logic, $offsetY="20", $offsetX="-30")

    Rel(API, State, "Sends heartbeat", "HTTPS")
    UpdateRelStyle(API, State, $offsetY="-30", $offsetX="-200")

    UpdateLayoutConfig($c4ShapeInRow="4", $c4BoundaryInRow="1")
```
