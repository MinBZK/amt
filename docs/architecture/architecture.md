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
Below is a context diagram of the Algorithm Management Toolkit, with some additional remarks about
its components.
```mermaid

C4Container
    title Container diagram for the Algorithm Management Toolkit System
    Person(user0, "User")


Boundary(b0, "Local") {
        Container_Ext(CLI, "CLI", "Command Line", "CLI to execute measures <br/> and instruments")
        Container_Ext(Tasks, "Tasks", "Python library", "Library containing executable tasks <br/> which are measures and instruments")
        System_Ext(InstrumentRegister, "Instrument Register",  "Contains information about <br/>how to execute instruments and measures")

    }



 Boundary(b1, "Algorithm Management Toolkit") {
        Container(FrontEnd, "Front End", "htmx, jinja2", "Provides user interface for projects <br/> and tasks")
        Container(Backend, "Back End", "FastAPI, Python","Includes the API application, <br/>business logic and system state")
        ComponentDb(Db, "Database")
        ContainerQueue(Message queue, "Message queue", "Redis")
        Component(Workers, "Workers", "Celery")

    }



Boundary(b2, "External"){
    System_Ext(Repository, "Repository", "External repository where the <br/> System Card will be stored")

}

UpdateLayoutConfig($c4ShapeInRow="1", $c4BoundaryInRow="4")

Rel(user0, CLI, "Executes tasks locally <br/>from", "Command line")
UpdateRelStyle(user0, CLI, $offsetY="-40", $offsetX="-140")

Rel(user0, FrontEnd, "Visits Algorithm Management<br/> Toolkit webpage", "HTTPS")
UpdateRelStyle(user0, FrontEnd, $offsetY="-40", $offsetX="-70")

Rel(CLI, Tasks, "Imports tasks from")
UpdateRelStyle(CLI, Tasks, $offsetY="-5", $offsetX="-120")

BiRel(FrontEnd, Backend, "Front End makes API calls, <br/> Back End sends live updates", "HTTPS, websocket")
UpdateRelStyle(FrontEnd, Backend, $offsetY="-10", $offsetX="-165")


BiRel(Backend, Db, "Reads from and <br/>writes to", "")
UpdateRelStyle(Backend, Db, $offsetY="-10", $offsetX="10")

BiRel(Backend, Message queue, "Submits tasks, <br/>gets results")
UpdateRelStyle(Backend, Message queue, $offsetY="80", $offsetX="15")


BiRel(Message queue, Workers, "Accepts tasks, <br/> writes progress")
UpdateRelStyle(Message queue, Workers, $offsetY="0", $offsetX="10")


Rel(Backend, Repository, "Writes System Card to", "")
UpdateRelStyle(Backend, Repository, $offsetY="20", $offsetX="-40")

Rel(Workers, Tasks, "Imports tasks <br/>from")
UpdateRelStyle(Workers, Tasks, $offsetY="160", $offsetX="60")

Rel(Tasks, InstrumentRegister, "Imports instructions from", "")
UpdateRelStyle(Tasks, InstrumentRegister, $offsetY="10", $offsetX="-150")

```

### Walkthrough
Suppose a user wants to perform a specific task from the Algoritmekader. To execute this task, the user has 2 options.

The first option is to execute the task locally by using the command line interface tool (CLI). The CLI tool imports the task from a Python library named `Tasks`. This library contains executable tasks that implement the measures and instruments from the `Instrument Register` (which are specified in the Algoritmekader). Instructions on how to perform these tasks are imported from the Instrument Register. There exists a one-to-one correspondence between measures and instruments in the `Instrument Register` and the task's within the `Tasks` library.

The second option is to use the Algorithm Management Toolkit (AMT). The user starts by visiting the Algorithm Management Toolkit website. Here, the user encounters a front end interface showing a planning board for projects and tasks. This planning board contains 3 columns: ‘To do’,  ‘Doing’ and ‘Done’. When a user drags a task from ’To do’ to ‘Doing’, the front end makes an API call to the back end of the AMT.

The backend consists of three components, showed in the component diagram at the end of this page.
1. An API application, which provides the project and tasks management functionality via HTTPS.
2. The business logic, which is the core logic of the AMT.
3. A system state, which provides the state of the AMT.

When receiving an API call, the API application forwards the instruction to the business logic. The business logic, in turn, updates the system state and submits the task to the Redis message queue. The message queue stores the task messages until a Celery worker is ready to process a specific task. When a Celery worker is available, it uses the task library to execute the task. After the task is completed by the worker, the result is sent back to the business logic via the message queue. The business logic now sends an update to the system state and writes the result to the database. Finally, the business logic writes a System Card to an external repository.

Meanwhile, the API application sends regular heartbeats to the system state to check for updates. The system state receives updates from the business logic and checks for updates by reading from the database. When a state is updated (for example, a task is "done" or "failed with error X"), the business logic returns this to the API application. Using a websocket, the API application sends live updates back to the front end, to make sure the planning board stays up to date.

## Component diagram of the back end of the Algorithm Management Toolkit
Below is a component diagram of the back end of the Algorithm Management Toolkit, with some additional remarks about its components.
```mermaid
C4Component
    title Component diagram for the back end of the Algorithm Management Toolkit System

 Boundary(b2, "Back End") {
        Container(State, "System State", "", "Provides the state of the <br/>Algorithm Management Toolkit")
        Container(Business Logic, "Business Logic", "Python", "Core logic of the <br/> Algorithm Management Toolkit")
        Container(API, "API Application", "Python, FastAPI", "Provides the project and task management <br/> functionality via HTTPS.")
    }



BiRel(API, Business Logic, "Forwards instructions, <br/> returns results", "")
UpdateRelStyle(API, Business Logic, $offsetY="-20", $offsetX="-110")

BiRel(State, Business Logic, "Gets / updates <br/>state", "")
UpdateRelStyle(State, Business Logic, $offsetY="-25", $offsetX="-35")

Rel(API, State, "Sends heartbeat", "HTTPS")
UpdateRelStyle(API, State, $offsetY="-10", $offsetX="-100")

UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="3")
```
