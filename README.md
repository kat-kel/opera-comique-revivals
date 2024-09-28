# opera-comique-revivals

Explorative data visualizations about revivals at the Opéra-Comique in the nineteenth century (with a focus on orchestration)

## Data architecture

```mermaid
erDiagram

    PERSON {
        varchar surname
        varchar given_names
        varchar wikidata_id
    }
    ACTION {
        boolean as_librettist
        boolean as_composer
        boolean as_adapter
        boolean as_arranger
    }
    ACTION }|--|{ PERSON : creative_actor
    ACTION }|--|{ PRODUCTION : work_produced
    PRODUCTION {
        varchar title
        integer number_of_acts
        boolean borrowed_music
        date first_performance
        varchar charlton_id
        boolean is_revision
    }
    PRODUCTION ||--o| PRODUCTION : based_on
    PERFORMANCE {
        date date
        varchar primarys_source
    }
    PERFORMANCE }|--|{ PRODUCTION : work_performed

```

### Person

An individual actor who created something.

|id| surname | given_names | wikidata_id |
|--|---|---|---|
|unique ID |last name|first name(s)|ID of person in WikiData database, if available|

### PRODUCTION

A creation, which can be known as a work. It includes original works, created by authors, as well as revisions of those works. It should not be confused with the English-language term "production" in the context of modern-day theater praxis, which refers to an interpretation of a work.

|id| title | based_on | number_of_acts | borrowed_music | first_performance | charlton_id | is_revision |
|--|---|---|---|---|---|---|---|
|unique ID|title according to Charlton and Wild dictionary (2005)| unique ID of the works on which this work is based, according to Charlton and Wild's dictionary | count of work's acts | whether the work has borrowed music, i.e. vaudevilles | date of the first performance, regardless of context, i.e. public and private | ID of the entry in Charlton and Wild's dictionary (2005)| whether the work is a revised version of a work |

### Action

A creative action involving an individual (Person) and which produced a work (Production).

|id|creative_actor|work_produced|as_librettist|as_composer|as_adapter|as_arranger|
|--|--|--|--|--|--|--|
|unique ID|unique ID of the person who created something|unique ID of the work to which the person contributed|whether the person's creative action was to write lyrics and/or dialogue for a new work|whether the person's creative action was to write music for a new work|whether the person's creative action was to rewrite lyrics and/or dialogue for a revised work|whether the person's creative action was to rewrite music for a revised work|

### Performance

The performance of a creative work (Production).

|id|date|work_performed|primary_source|
|--|--|--|--|
|unique ID|date of the performance|work performed on this day|primary source attesting to the performance|
