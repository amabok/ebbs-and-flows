# Ebbs and flows
<img src="./docs/images/ebbs-and-flows-sv-screenshot.jpg" width="250"/>

A simple library for running linear flows of tasks with persistence, failsafe and retries/re-runs in mind.

## Main Concepts and building blocks
In Ebbs And Flows everything revolves around the following Entities that you can find in the flows.py module under the model package.

### Task and TaskExecution
The Task is the minimum building block of the Ebbs and Flows library. It's here that the code - the powerhouse part of the flow - is executed. Tasks implement a single method called ```run``` that either return an ```ExecutionContext``` holding some overall execution state and results (more on that later) or throw an exception instead. The ```output``` member of the ```TaskExecution``` entity will hold detailed information on the reasons behind the nature of the failure of the Task.
Task classes implementations should ideally not hold any state as their instances are shared between every ```FlowTemplate``` instance more on that on [the Flow section](#flow-flow-template-and-flow-execution). 

![Tasks](/docs/images/tasks.png)


In the first case we say that the Task executed with Success (TaskStatus.SUCCEEDED) in the latter we consider that it Failed (TaskStatus.FAILED)

![Task Statuses](/docs/images/task_execution_states.png)


### Execution Context
The current state of the flow execution is captured in the ```ExecutionContext```. This entity holds all  relevant pieces of data that traverses through a flow execution. 
The ExecutionContext allows storage and retrieval of Python Objects that are relevant pieces of data of shared interest for the flow execution steps (the Tasks). These pieces of data are identified by an unique name. If one tries to add an already existing entry with the same identifier a ValueError will be raised.

![Tasks](/docs/images/execution_context.png)

Each task takes an ExecutionContext as input and must return an ExecutionContext as output. The input ExecutionContext should not be modified and the Task should return a novel ExecutionContext object in the output containing the necessary data objects that a specific task might create. It's also acceptable that a specific task doesn't create new pieces of data in the output ExecutionContext. It's good practice that a copy of the input ExecutionContext is returned in the output.

### Flow, Flow Template and Flow Execution
Flows are really not an entity in the library but they representation is encapsulated in what we call a ```FlowTemplate```. In order to run a Flow one can instantiate a ```FlowTemplate``` and proceed to add Task instances in order to build your Flow logic.
Flow Templates are then akin to a blueprint for execution. Every ```FlowExecution``` can have the following FlowStatus transitions.

![FlowStatuses](/docs/images/flow_execution_states.png)

## Architecture 

The architecture of the library is quite simple and relies on the following components that interact in a manner depicted in the diagram below.

![Tasks](/docs/images/architecture.png)

### FlowRunner
The FlowRunner provides you with methods that enables you to perform the following operations:
- Register a Flow Template: this operation is needed beforehand so that the FlowRunner knows which Tasks from a Flow needs to be run. This registry is not persisted and stays in memory as long as the FlowRunner instance lives.

- Get Flow Template: gets a flow template per name. Duplicated flow template names are not allowed.

- Schedule/Re Schedule Flow: Allows to Schedule the execution of a flow. In case the flow is in a failed state it can be re-scheduled by using the ```reschedule_flow_execution```.

- Ru/Rerun Flow: Runs/Re-runs one flow by picking one from the ones in Scheduled state

- Task related methods: they do exist in the FlowRunner but they pertain mainly to internal FlowRunner logic. Use them at your own risk/convenience.


### FlowService
- The FlowService encapsulates all the business logic needed to maintain the consistency of the Tasks and Flows.
- Direct usage of the methods is encouraged - for querying purposes - but changes and custom logic change should be made with caution.

### FlowRepository
- The persistence layer of the FlowService. Once again, and following up on the observations in the section above, unless doing any custom made developments (mainly for querying) and changes to core logic, no direct access should be needed at this level.

## How does this all tie togheter
- Leverage the features of the ```FlowRunner``` to coordinate and instruct ```FlowTemplate``` executions. Sticking to the usage of the ```FlowRunner``` will cover most of the cases you need for basic usage. You can also use the features from the ```FlowService``` to query the current status of the Flow running engine. You shall not need to touch the ```FlowRepository``` unless building new features for the ```FlowService``` or in case you need to perform specific queries suited to your needs.
That falls in the realm of custom developments and further extending the library which diverges out of the scope of this first version.

- From the members names of the main Entity classes it should be quite straightforward to understand their usage. In case there is some uncertainty on the purpose and goal of certain fields please refer to the Unit/Integration tests under the ```tests``` folder in order to clarify their usage.

# Development topics
## Pre-requisites 
- Python 3.10 installed

## Setting the development environment
- ```python -m venv development``` 
- activate the virtual environment ```development\Scripts\activate```
- pip install -r requirements.txt

## Running the test suite
- Run ```pytest -v```