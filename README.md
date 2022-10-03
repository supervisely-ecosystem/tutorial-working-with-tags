# All about Tags

[Read this tutorial in developer portal.](https://developer.supervise.ly/advanced-user-guide/all-about-tags)

## Introduction

In this tutorial we will be focusing on working with tags using Supervisely SDK. We'll go through complete cycle from creating TagMeta to assigning Tags to images and objects directly.

You will learn:
1) how to create tags for different tasks and scenarios with various parameters.
2) how to add tags to project
3) how to assign tags to images and objects

📗 Everything you need to reproduce [this tutorial is on GitHub](https://github.com/supervisely-ecosystem/tutorial-working-with-tags): source code and demo data.

## How to debug this tutorial

**Step 1.** Prepare `~/supervisely.env` file with credentials. [Learn more here.](https://developer.supervise.ly/getting-started/basics-of-authentication#how-to-use-in-python)



**Step 2.** Clone [repository](https://github.com/supervisely-ecosystem/tutorial-working-with-tags) with source code and demo data and create [Virtual Environment](https://docs.python.org/3/library/venv.html).

```bash
git clone https://github.com/supervisely-ecosystem/tutorial-working-with-tags
cd tutorial-working-with-tags
./create_venv.sh
```

**Step 3.** Open repository directory in Visual Studio Code.&#x20;

```bash
code -r .
```

**Step 4.** Get **[Lemons (Annotated)](https://ecosystem.supervise.ly/projects/lemons-annotated)** project from ecosystem. Lemons (Annotated) is an example project with annotated lemons and kiwi fruits, with 6 images in it.

![Get project from Ecosystem](https://user-images.githubusercontent.com/48913536/193692418-731fa985-4958-4a42-893a-411e558faa04.png)

**Step 5.** change ✅ project ID ✅ in `local.env` file by copying the ID from the context menu of the project.

```python
CONTEXT_PROJECTID=111 # ⬅️ change value
```

![Copy project ID from context menu](https://user-images.githubusercontent.com/48913536/193692408-6a1ba506-751b-4634-937e-3f2cebc2b22c.png)

**Step 6.** Start debugging `src/main.py`&#x20;

## **Part 1.** Tag Meta

### Import libraries

```python
import os
from dotenv import load_dotenv
import supervisely as sly
```

### Init API client

Init API for communicating with Supervisely Instance. First, we load environment variables with credentials and project ID:

```python
load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))
api = sly.Api()
```

### Create Tag Meta

In order to create Tag itself you must create TagMeta object with parameters such as:
* name: string (required)
* value_type: sly.TagValueType (required)
* color: List[int]
* applicable_to:  sly.TagApplicableTo
* applicable_classes: List[str]

Let's start with creating a simple TagMeta for Lemon. 
This TagMeta object can be applied to both images and objects, and also to any class

```python
lemon_tag_meta = sly.TagMeta(name="lemon", value_type=sly.TagValueType.NONE)
print(lemon_tag_meta)
# Name:  lemon
# Value type:none
# Possible values:None
# Hotkey
# Applicable toall
# Applicable classes[]
```

Let's change applicable classes of this TagMeta to class "lemon" only and make it applicable only to objects.
We can recreate TagMeta or clone already existing TagMeta with additional parameters.
Most supervisely classes are immutable, so you have to assign or reassign them to variables.

```python
lemon_tag_meta = lemon_tag_meta.clone(
    applicable_to=sly.TagApplicableTo.OBJECTS_ONLY, applicable_classes=["lemon"]
)
print(lemon_tag_meta)
# Name:  lemon
# Value type:none
# Possible values:None
# Hotkey
# Applicable toobjectsOnly
# Applicable classes['lemon']
```

Now let's create a TagMeta for "kiwi" with "oneof_string" value type

```python
possible_kiwi_values = ["fresh", "ripe", "old", "rotten"]
kiwi_tag_meta = sly.TagMeta(
    name="kiwi",
    applicable_to=sly.TagApplicableTo.OBJECTS_ONLY,
    value_type=sly.TagValueType.ONEOF_STRING,
    possible_values=possible_kiwi_values,
)
print(kiwi_tag_meta)
# Name:  kiwi
# Value type:oneof_string
# Possible values:['fresh', 'ripe', 'old', 'rotten']
# Hotkey
# Applicable toall
# Applicable classes[]
```

Now we create a tag meta with "any_number" value type for counting total fruits on image.

```python
fruits_count_tag_meta = sly.TagMeta(
    "fruits count",
    value_type=sly.TagValueType.ANY_NUMBER,
    applicable_to=sly.TagApplicableTo.IMAGES_ONLY,
)
print(fruits_count_tag_meta)
# Name:  fruits count
# Value type:any_number
# Possible values:None
# Hotkey
# Applicable toimagesOnly
# Applicable classes[]
```

Bring all created tag metas together in a list

```python
tag_metas = [lemon_tag_meta, kiwi_tag_meta, fruits_count_tag_meta]
```

## **Part 2.** Add TagMetas to project

Get project meta from server

```python
project_id = int(os.environ["CONTEXT_PROJECTID"])
project_meta_json = api.project.get_meta(id=project_id)
project_meta = sly.ProjectMeta.from_json(data=project_meta_json)
```

![Project Meta before adding Tags](https://user-images.githubusercontent.com/48913536/193692433-806cb981-cc12-4d60-af25-9777b2bfe3f5.png)


Check that created Tag Metas for lemon and kiwi don't already exist in project meta, and if not, add them to project meta.

```python
for tag_meta in tag_metas:
    if tag_meta not in project_meta.tag_metas:
        project_meta = project_meta.add_tag_meta(new_tag_meta=tag_meta)
```

Update project meta on Supervisely instance after adding Tag Metas to project meta.

```python
api.project.update_meta(id=project_id, meta=project_meta)
```

![Updated Tags](https://user-images.githubusercontent.com/48913536/193692445-0179e903-9591-4525-95fe-0d8a5eb35aed.png)

## **Part 3.** Create Tags from Tag Metas and update annotation on server

```python
# get list of datasets by project id
datasets = api.dataset.get_list(project_id)
dataset_ids = [dataset.id for dataset in datasets]
# cycle through all images in project datasets
for dataset_id in dataset_ids:
    # get list of images in dataset by id
    images_infos = api.image.get_list(dataset_id=dataset_id)
    for image_info in images_infos:
        # get image id from image info
        image_id = image_info.id

        # check image tags
        image_tags = image_info.tags
        print(f"{image_info.name} tags: {image_tags}")

        # download annotation
        ann_json = api.annotation.download_json(image_id=image_id)
        ann = sly.Annotation.from_json(data=ann_json, project_meta=project_meta)
        
        # create and assign Tag to image
        fruits_count_tag = sly.Tag(meta=fruits_count_tag_meta, value=len(ann.labels))
        ann = ann.add_tag(fruits_count_tag)

        # cycle through objects in annotation and assign appropriate tag
        new_labels = []
        for label in ann.labels:
            new_label = None
            if label.obj_class.name == "lemon":
                lemon_tag = sly.Tag(meta=lemon_tag_meta)
                new_label = label.add_tag(lemon_tag)
            elif label.obj_class.name == "kiwi":
                kiwi_tag = sly.Tag(meta=kiwi_tag_meta, value="fresh")
                new_label = label.add_tag(kiwi_tag)
            if new_label:
                new_labels.append(new_label)

        # upload updated ann to Supervisely instance
        ann = ann.clone(labels=new_labels)
        api.annotation.upload_ann(img_id=image_id, ann=ann)
```

![Result](https://user-images.githubusercontent.com/48913536/193692460-edcd4767-343d-409a-b312-8dc047de1baf.png)

# Advanced API

Advanced API allows user to add tags directly to images or objects without downloading annotation data from server.

### Add Tag directly to image

Get project meta again after updating it with new tags

```python
project_meta_json = api.project.get_meta(id=project_id)
project_meta = sly.ProjectMeta.from_json(data=project_meta_json)
```

Get image tag ID from project meta

```python
image_tag_id = project_meta.get_tag_meta(fruits_count_tag_meta.name).sly_id
```

Add Tag to image using Tag supervisely ID from project meta

```python
api.image.add_tag(image_id=image_id, tag_id=image_tag_id, value=7)
```

### Add Tags to objects directly

```python
ann_json = api.annotation.download_json(image_id=image_id)
ann = sly.Annotation.from_json(data=ann_json, project_meta=project_meta)
# Cycle through objects in annotation and add appropriate tag
for label in ann.labels:
    # Get figure sly id
    figure_id = label.geometry.sly_id
    if label.obj_class.name == "lemon":
        # Get tag sly id
        tag_meta_id = project_meta.get_tag_meta(lemon_tag_meta.name).sly_id
        api.advanced.add_tag_to_object(tag_meta_id=tag_meta_id, figure_id=figure_id)
    elif label.obj_class.name == "kiwi":
        tag_meta_id = project_meta.get_tag_meta(kiwi_tag_meta.name).sly_id
        api.advanced.add_tag_to_object(tag_meta_id=tag_meta_id, figure_id=figure_id, value="fresh")
```
