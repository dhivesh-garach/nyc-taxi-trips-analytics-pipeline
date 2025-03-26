terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.25.0"
    }
  }
}

provider "google" {
  project = "nyc-taxi-analytics-pipeline"
  region  = "asia-south2-c"
}

resource "google_storage_bucket" "taxi-rides" {
  name          = "taxi-rides-ntap"
  location      = "ASIA-SOUTH2"
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

resource "google_bigquery_dataset" "taxi_rides_ny" {
  dataset_id = "taxi_rides_ny"
  location = "asia-south2"
  delete_contents_on_destroy = true
}