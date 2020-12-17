@JsonSerializable()
class IssueList {
    List<Issue> issues;
    int total_count;
    int offset;
    int limit;

    IssueList(this.issues,this.total_count,this.offset,this.limit);
    factory IssueList.fromJson(Map<String, dynamic> json) => _$IssueListFromJson(json);
    Map<String, dynamic> toJson() => _$IssueListToJson(this);
}


@JsonSerializable()
class Issue {
    int id;
    Project project;
    Tracker tracker;
    Status status;
    Priority priority;
    Author author;
    String subject;
    String description;
    String start_date;
    dynamic due_date;
    int done_ratio;
    bool is_private;
    dynamic estimated_hours;
    List<CustomField> custom_fields;
    String created_on;
    String updated_on;
    dynamic closed_on;

    Issue(this.id,this.project,this.tracker,this.status,this.priority,this.author,this.subject,this.description,this.start_date,this.due_date,this.done_ratio,this.is_private,this.estimated_hours,this.custom_fields,this.created_on,this.updated_on,this.closed_on);
    factory Issue.fromJson(Map<String, dynamic> json) => _$IssueFromJson(json);
    Map<String, dynamic> toJson() => _$IssueToJson(this);
}


@JsonSerializable()
class Project {
    int id;
    String name;

    Project(this.id,this.name);
    factory Project.fromJson(Map<String, dynamic> json) => _$ProjectFromJson(json);
    Map<String, dynamic> toJson() => _$ProjectToJson(this);
}


@JsonSerializable()
class Tracker {
    int id;
    String name;

    Tracker(this.id,this.name);
    factory Tracker.fromJson(Map<String, dynamic> json) => _$TrackerFromJson(json);
    Map<String, dynamic> toJson() => _$TrackerToJson(this);
}


@JsonSerializable()
class Status {
    int id;
    String name;

    Status(this.id,this.name);
    factory Status.fromJson(Map<String, dynamic> json) => _$StatusFromJson(json);
    Map<String, dynamic> toJson() => _$StatusToJson(this);
}


@JsonSerializable()
class Priority {
    int id;
    String name;

    Priority(this.id,this.name);
    factory Priority.fromJson(Map<String, dynamic> json) => _$PriorityFromJson(json);
    Map<String, dynamic> toJson() => _$PriorityToJson(this);
}


@JsonSerializable()
class Author {
    int id;
    String name;

    Author(this.id,this.name);
    factory Author.fromJson(Map<String, dynamic> json) => _$AuthorFromJson(json);
    Map<String, dynamic> toJson() => _$AuthorToJson(this);
}


@JsonSerializable()
class CustomField {
    int id;
    String name;
    dynamic value;

    CustomField(this.id,this.name,this.value);
    factory CustomField.fromJson(Map<String, dynamic> json) => _$CustomFieldFromJson(json);
    Map<String, dynamic> toJson() => _$CustomFieldToJson(this);
}
