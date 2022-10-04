import os
from dotenv import load_dotenv
import supervisely as sly

load_dotenv("local.env")
load_dotenv(os.path.expanduser("~/supervisely.env"))
api = sly.Api()

####################
# Part 1: Tag Meta #
####################

# Let's start with creating a simple TagMeta for Lemon
# This TagMeta object can be applied to both images and objects, and also to any class
lemon_tag_meta = sly.TagMeta(name="lemon", value_type=sly.TagValueType.NONE)

# Let's change applicable classes of this TagMeta to class "lemon" only and make it applicable only to objects
# We can recreate TagMeta or clone already existing TagMeta with additional parameters
lemon_tag_meta = lemon_tag_meta.clone(
    applicable_to=sly.TagApplicableTo.OBJECTS_ONLY, applicable_classes=["lemon"]
)

# Now let's create a TagMeta for "kiwi" with "oneof_string" value type
possible_kiwi_values = ["small", "medium", "big"]
kiwi_tag_meta = sly.TagMeta(
    name="kiwi",
    applicable_to=sly.TagApplicableTo.OBJECTS_ONLY,
    value_type=sly.TagValueType.ONEOF_STRING,
    possible_values=possible_kiwi_values,
)

# Now we create a TagMeta with "any_number" value type for counting fruits on image
fruits_count_tag_meta = sly.TagMeta(
    name="fruits count",
    value_type=sly.TagValueType.ANY_NUMBER,
    applicable_to=sly.TagApplicableTo.IMAGES_ONLY,
)


# and one more TagMeta with "any_string" value type to enter the origin of the fruit into it
fruit_origin_tag_meta = sly.TagMeta(
    name="imported from",
    value_type=sly.TagValueType.ANY_STRING,
    applicable_to=sly.TagApplicableTo.OBJECTS_ONLY,
    applicable_classes=["lemon", "kiwi"],
)


# Bring all created TagMetas together in TagMetaCollection or list
tag_metas = [
    lemon_tag_meta,
    kiwi_tag_meta,
    fruits_count_tag_meta,
    fruit_origin_tag_meta,
]

###################################
# Part 2. Add TagMetas to project #
###################################

# Get project meta from server
project_id = int(os.environ["CONTEXT_PROJECTID"])
project_meta_json = api.project.get_meta(id=project_id)
project_meta = sly.ProjectMeta.from_json(data=project_meta_json)

# Check that our created tag metas for lemon and kiwi don't exist already in project meta
# And if not, add them to project meta
for tag_meta in tag_metas:
    if tag_meta not in project_meta.tag_metas:
        project_meta = project_meta.add_tag_meta(new_tag_meta=tag_meta)

# Update project meta on Supervisely instance after adding
# Tag Metas to project meta
api.project.update_meta(id=project_id, meta=project_meta)

######################################################################
# Part 3. Create Tags from Tag Metas and update annotation on server #
######################################################################

# get list of datasets in our project
datasets = api.dataset.get_list(project_id)
dataset_ids = [dataset.id for dataset in datasets]
# iterate over all images in project datasets
for dataset_id in dataset_ids:
    # get list of images in dataset by id
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
                lemon_tag = sly.Tag(meta=lemon_tag_meta)
                origin_tag = sly.Tag(meta=fruit_origin_tag_meta, value="Spain")
                new_label = label.add_tags([lemon_tag, origin_tag])
            elif label.obj_class.name == "kiwi":
                kiwi_tag = sly.Tag(meta=kiwi_tag_meta, value="medium")
                origin_tag = sly.Tag(meta=fruit_origin_tag_meta, value="Italy")
                new_label = label.add_tags([kiwi_tag, origin_tag])
            if new_label:
                new_labels.append(new_label)

        # upload updated ann to Supervisely instance
        ann = ann.clone(labels=new_labels)
        api.annotation.upload_ann(img_id=image_id, ann=ann)
