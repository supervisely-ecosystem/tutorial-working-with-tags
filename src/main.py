import os
from dotenv import load_dotenv
import supervisely as sly

load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))
api = sly.Api()

####################
# Part 1: Tag Meta #
####################

# Let's start with createing a simple TagMeta
fruit_tag_meta = sly.TagMeta(
    name="fruits",
    applicable_to=sly.TagApplicableTo.OBJECTS_ONLY,
    value_type=sly.TagValueType.NONE,
)

# Now let's create a simple TagMeta for fruit name
fruit_name_tag_meta = sly.TagMeta(
    name="name",
    applicable_to=sly.TagApplicableTo.OBJECTS_ONLY,
    value_type=sly.TagValueType.ANY_STRING,
    applicable_classes=["lemon", "kiwi"],
)

# Now let's create a TagMeta for "kiwi" with "oneof_string" value type
fruit_size_tag_meta = sly.TagMeta(
    name="size",
    applicable_to=sly.TagApplicableTo.OBJECTS_ONLY,
    value_type=sly.TagValueType.ONEOF_STRING,
    possible_values=["small", "medium", "big"],
)

# Now we create a TagMeta with "any_number" value type for counting fruits on image
fruit_origin_tag_meta = sly.TagMeta(
    name="imported_from",
    value_type=sly.TagValueType.ANY_STRING,
    applicable_to=sly.TagApplicableTo.OBJECTS_ONLY,
    applicable_classes=["lemon", "kiwi"],
)


# and one more TagMeta with "any_string" value type to enter the origin of the fruit into it
fruits_count_tag_meta = sly.TagMeta(
    name="fruits_count",
    value_type=sly.TagValueType.ANY_NUMBER,
    applicable_to=sly.TagApplicableTo.IMAGES_ONLY,
)


# Bring all created TagMetas together in TagMetaCollection or list
tag_metas = [
    fruit_tag_meta,
    fruit_name_tag_meta,
    fruit_size_tag_meta,
    fruit_origin_tag_meta,
    fruits_count_tag_meta,
]

###################################
# Part 2. Add TagMetas to project #
###################################

# Get project meta from server
project_id = sly.env.project_id()
project_meta_json = api.project.get_meta(id=project_id)
project_meta = sly.ProjectMeta.from_json(data=project_meta_json)

# Check that our created tag metas for lemon and kiwi don't exist already in project meta
# And if not, add them to project meta
for tag_meta in tag_metas:
    if tag_meta not in project_meta.tag_metas:
        project_meta = project_meta.add_tag_meta(new_tag_meta=tag_meta)

# Update project meta on Supervisely instance after adding
# Tag Metas to project meta and get updated project meta
api.project.update_meta(id=project_id, meta=project_meta)
project_meta_json = api.project.get_meta(id=project_id)
project_meta = sly.ProjectMeta.from_json(data=project_meta_json)

######################################################################
# Part 3. Create Tags and update annotation on server #
######################################################################

# get list of datasets in our project
datasets = api.dataset.get_list(project_id)
dataset_ids = [dataset.id for dataset in datasets]
# iterate over all images in project datasets
for dataset_id in dataset_ids:
    # get list of images in dataset
    images_infos = api.image.get_list(dataset_id=dataset_id)
    for image_info in images_infos:
        # get image id from image info
        image_id = image_info.id

        # download annotation
        ann_json = api.annotation.download_json(image_id=image_id)
        ann = sly.Annotation.from_json(data=ann_json, project_meta=project_meta)

        # create and assign Tag to image
        fruits_count_tag = sly.Tag(meta=fruits_count_tag_meta, value=len(ann.labels))
        ann = ann.add_tag(fruits_count_tag)

        # iterate over objects in annotation and assign appropriate tag
        new_labels = []
        for label in ann.labels:
            new_label = None
            if label.obj_class.name == "lemon":
                name_tag = sly.Tag(meta=fruit_name_tag_meta, value="lemon")
                size_tag = sly.Tag(meta=fruit_size_tag_meta, value="medium")
                origin_tag = sly.Tag(meta=fruit_origin_tag_meta, value="Spain")
                new_label = label.add_tags([name_tag, size_tag, origin_tag])
            elif label.obj_class.name == "kiwi":
                name_tag = sly.Tag(meta=fruit_name_tag_meta, value="kiwi")
                size_tag = sly.Tag(meta=fruit_size_tag_meta, value="small")
                origin_tag = sly.Tag(meta=fruit_origin_tag_meta, value="Italy")
                new_label = label.add_tags([name_tag, size_tag, origin_tag])
            if new_label:
                new_labels.append(new_label)

        # update and upload ann to Supervisely instance
        ann = ann.clone(labels=new_labels)
        api.annotation.upload_ann(img_id=image_id, ann=ann)

    # get tag meta from project meta
    tag_meta = project_meta.get_tag_meta("fruits")

    # create a list of images ids from images infos
    image_ids = [image_info.id for image_info in images_infos]

    # get tag meta id
    tag_meta_id = tag_meta.sly_id

    # update tags in batches.
    api.image.add_tag_batch(image_ids, tag_meta_id, value=None, tag_meta=tag_meta)
