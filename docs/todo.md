---
title: Todo Lists
nav_order: 9
---

# Todo Lists

One Todo List entity is created for each task list on the user account. Each sensor shows the number of incomplete tasks as the status of the sensor. The `all_tasks` attribute is an array of incomplete tasks. The `overdue_tasks` attribute shows any tasks which have a due date and are overdue as an array.

### Display
In order to show the tasks in the front end, a markdown card can be used. The following is an example that allows you to display a bulleted list subject from the `all_tasks` array of tasks.

```yaml
type: markdown
title: Tasks
content: |-
  {% raw %}{% for task in state_attr('sensor.tasks_sc_personal', 'all_tasks') -%}
  - {{ task['subject'] }}
  {% endfor %}{% endraw %}
```