Create a solution based on claude code and claude skills to build and maintain Angular applications

* Create skills to build and modify angular objects
* Generate build commands from an Open API schema

# Skills

Section will break down the "skills" requirement into the different skills.

Each skill will include:
- A building script(s).
- A description of the skill, including when to use it and how to use it.
  - Optionally additional details about the skill or sub section, in seperate md files.
- Template files.
Each script will have the following modes:
- Create: from zero, the object didn't exist before.
- Modify: Modify a given object
- Delete: Delete the object

## Angular Material workspace boiler plate

Manage an Angular workspace area
- Create: Create an Angular Material workspace from scratch
- Modify: Changes might be: NPM packages, configuration parameters, new workspace methodologies and tools like build or test, new BKMs arising from an Angular version change.
- Delete: When entering an old area, and required to start from scratch it's better to Delete and Create than modify.

## Angular Material app boiler plate

Manage an Angular Material app 
- Create: Create an Angular Material workspace from scratch
- Modify: Changes might be: NPM packages, configuration parameters, new workspace methodologies and tools like build or test, new BKMs arising from an Angular version change.
- Delete: When entering an old area, and required to start from scratch it's better to Delete and Create than modify.

## Angular API generation

Manage Angular data model API, using ng-openapi-gen
- Create: Generate data model from scratch
- Modify: Make changes to an existing data model
- Delete: When it is too complex to modify successfully it's better to delete and generate from scratch.

## Angular data model Service

Manage Angular data model API service
- Create: Generate the service
- Modify: Modify the service if changes made in Angular forced changes related to this service
- Delete: When it's too complex to modify we delete and create.

## Angular Material small field level component generation
Manage Angular Material small component generation
- Create: Generate a component from scratch
- Modify: Modify an existing component
- Delete: When it's too complex to modify we delete and create.

## Angular Material form field generation
Manage Angular Material form field generation
- Create: Generate a form field from scratch
- Modify: Modify an existing form field
- Delete: When it's too complex to modify we delete and create.

## Angular component generation
Manage Angular component generation
- Create: Generate a component from scratch
- Modify: Modify an existing component
- Delete: When it's too complex to modify we delete and create.

## Angular Material complex component generation
Manage Angular Material complex component generation, including mixins, nested components, and complex cross component interactions
- Create: Generate a complex component from scratch
- Modify: Modify an existing complex component
- Delete: When it's too complex to modify we delete and create.

## Angular Material reactive form generation
Manage Angular Material reactive form generation
- Create: Generate a reactive form from scratch
- Modify: Modify an existing reactive form
- Delete: When it's too complex to modify we delete and create.

## Angular Material page generation
Manage Angular Material page (like "Landing Page", "Dashboard", "Profile Page", etc.) generation, including routing and navigation
- Create: Generate a page from scratch
- Modify: Modify an existing page
- Delete: When it's too complex to modify we delete and create.

## Angular Material site generation
Manage Angular Material site generation, including multiple pages, routing, navigation, and shared components
- Create: Generate a site from scratch
- Modify: Modify an existing site
- Delete: When it's too complex to modify we delete and create.

---

# Skill building

Each skill building will include the following steps:
1. Define the skill and its purpose.
2. Identify the necessary inputs and outputs for the skill.
3. Develop the building script(s) for the skill, ensuring they can handle the create, modify, and delete modes effectively.
4. Create reusable templates that can be used by the building scripts to generate the necessary code or configurations for the skill.
5. Test the skill to ensure it works as expected in all modes (create, modify, delete).

## 1. Define the skill and its purpose
## 2. Identify the necessary inputs and outputs for the skill
## 3. Develop the building script(s) for the skill
## 4. Create reusable templates that can be used by the building scripts to generate the necessary code or configurations for the skill
## 5. Test the skill to ensure it works as expected in all modes (create, modify, delete)

