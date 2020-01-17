# Build required Lambda Layers
This directory contains the necessary Dockerfile files to build the Lambda Layers required by the
spam detection pipeline.

Lambda Layers are a way of separating out large dependencies (such as third-party libraries) from your
Lambda code.  You can create a Layer once and just reference it when you create your Lambda.  For example,
the `detect-bad-known-content` Lambda requires a perceptual image hashing algorithm implemented in the
`ImageHash` Python module.  With its dependencies, this represents 55MB of compressed code, and almost 190MB
uncompressed.  It would be extremely inefficient to merge that code in with our `detect-bad-known-content`
Lambda implementation and upload to it to AWS.  Instead, we define a Layer containing the `ImageHash` module
and reference it when we upload the `detect-bad-known-content` Lambda implementation.

If you are creating a new instance of the spam detection pipeline on a new AWS account, you will have to
create and upload this Layer.  Follow these instructions to do so:

1.  Create a zip file containing the module and its dependencies.

    In this directory, run the following commands:
    ```
    docker build -f Dockerfile.imagehash -t imagehash-layer:latest .
    docker run -v `pwd`:/output imagehash-layer:latest
    ```

    This should result in a file called `imagehash-layer.zip` being created in this directory.

2.  Upload `imagehash-layer.zip` to an S3 bucket where you will be creating running the Lambdas.

    It does not seem like you need to set any special permisions on the bucket or S3 file.  It does
    not have to be public, etc.

3.  Create the Lambda Layer via the AWS Console.

    You need to click on the Lambda server, and then select Layers from the left nav tab.

    Click "Create Layer", specifying the URL for the `imagehash-layer.zip`.  Select Python 3.7 as
    the support environment.

    Find and copy the ARN for the Lambda Layer Version.

4.  Update your `IMAGE_HASH_LAYER_ARN` environment variable to the new ARN.
